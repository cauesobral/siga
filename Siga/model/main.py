from __future__ import annotations

import json
import os
import sys
import threading
import tkinter as tk
from collections.abc import Callable
from datetime import date, datetime
from tkinter import messagebox, ttk
from typing import Any, ClassVar

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "model"))

VERDE: str = "#1a8a1a"
VERDE_ESCURO: str = "#126b12"
VERDE_CLARO: str = "#d5ecd5"
FUNDO: str = "#f2f2f2"
CINZA: str = "#e8e8e8"
BORDA: str = "#dcdcdc"
FONTE: str = "Helvetica"
TIPOS_CARGA: list[str] = ["Contêineres", "Granel", "Petróleo"]
PORTOS: list[str] = ["Porto de Santos", "Porto do Rio de Janeiro",
                     "Porto de Paranaguá", "Porto de Suape"]
CFG_PATH: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configuracoes.json")
USUARIOS_PATH: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usuarios.json")


def _carregar_usuarios() -> list[dict[str, str]]:
    """Lê usuarios.json e retorna lista de dicts {nome, senha, porto}."""
    if not os.path.exists(USUARIOS_PATH):
        return []
    try:
        with open(USUARIOS_PATH, "r", encoding="utf-8") as f:
            dados: list[dict[str, str]] = json.load(f)
        return dados
    except (json.JSONDecodeError, ValueError):
        return []

from Berco import Berco
from Carga import Carga
from CondicaoClimatica import CondicaoClimatica
from EventoDeRisco import EventoDeRisco, NivelDeImpacto
from Gerenciador import GerenciadorDeAtracacao
from Historico import Historico
from JanelaDeMare import JanelaDeMare
from Navio import Navio
from PoliticaDeAtracacao import (PoliticaDeAtracacao, PorMare, PorOrdemDeChegada,
                                  PorPrioridadeDeCarga)
from StatusOperacional import StatusOperacional
import Repositorio



PROFUNDIDADE_CANAL: float = 15.0
PRIORIDADE_POR_TIPO: dict[str, int] = {"petróleo": 0, "granel": 1, "contêineres": 2}
POLITICAS: dict[str, PoliticaDeAtracacao] = {
    p.get_nome(): p
    for p in (PorMare(), PorPrioridadeDeCarga(PRIORIDADE_POR_TIPO), PorOrdemDeChegada())
}
COR_STATUS: dict[str, str] = {"Normal": "#1a8a1a", "Atenção": "#d4a000", "Risco Alto": "#c0392b"}


# ── widget toggle on/off ──────────────────────────────────────────────────────
class _Toggle(tk.Canvas):
    _W: ClassVar[int] = 44
    _H: ClassVar[int] = 24

    def __init__(self, pai: tk.Misc, var: tk.BooleanVar, bg: str = "white") -> None:
        super().__init__(pai, width=self._W, height=self._H,
                         bg=bg, highlightthickness=0, cursor="hand2")
        self._var = var
        self._redraw()
        self.bind("<Button-1>", lambda _e: self._toggle())
        self._var.trace_add("write", self._on_change)

    def _on_change(self, _n: str, _i: str, _m: str) -> None:
        try:
            if self.winfo_exists():
                self._redraw()
        except tk.TclError:
            pass

    def _toggle(self) -> None:
        self._var.set(not self._var.get())

    def _redraw(self) -> None:
        self.delete("all")
        on = self._var.get()
        cor = VERDE if on else "#b0b0b0"
        h = self._H
        self.create_oval(2, 2, h - 2, h - 2, fill=cor, outline="")
        self.create_oval(self._W - h + 2, 2, self._W - 2, h - 2, fill=cor, outline="")
        self.create_rectangle(h // 2, 2, self._W - h // 2, h - 2, fill=cor, outline="")
        r = h // 2 - 3
        cx = self._W - h // 2 if on else h // 2
        self.create_oval(cx - r, 3, cx + r, h - 3, fill="white", outline="")


# ── aplicação ─────────────────────────────────────────────────────────────────
class App(tk.Tk):
    botoes: dict[str, tk.Button]
    l_titulo: tk.Label
    conteudo: tk.Frame
    escolhida: tk.StringVar
    previa: tk.Frame
    fila: list[Navio]
    bercos: list[Berco]
    widgets_politica: dict[str, tuple[tk.Frame, tk.Label, tk.Label]]

    def __init__(self) -> None:
        super().__init__()
        self.title("SIGA - Sistema Inteligente de Gestão de Atracações")
        self.geometry("1100x640")
        self.minsize(960, 580)
        self.configure(bg=VERDE_ESCURO)

        # sessão
        self.operador: str = ""
        self.porto: str = PORTOS[0]

        # estado (fila/bercos carregados após login com o porto correto)
        self.politica_ativa: str | None = None
        self._eventos_api: list[EventoDeRisco] = []  # dados brutos da API
        self.eventos: list[EventoDeRisco] = []        # após aplicação dos limiares
        self.fila:   list[Navio] = []
        self.bercos: list[Berco] = []
        self.historico = Historico()
        self.gerenciador = GerenciadorDeAtracacao(self.historico)
        self.tela_atual: tuple[str, Callable[[tk.Frame], None]] | None = None
        self.clima_texto = tk.StringVar(value="Clima: carregando...")

        # configurações (carregadas do JSON se existir)
        self.cfg_mare_min = tk.DoubleVar(value=1.0)
        self.cfg_vento = tk.DoubleVar(value=60.0)
        self.cfg_chuva = tk.DoubleVar(value=50.0)
        self.cfg_confirmar_politica = tk.BooleanVar(value=True)
        self.cfg_notif_nova = tk.BooleanVar(value=True)
        self.cfg_notif_sem_espaco = tk.BooleanVar(value=False)
        self.cfg_notif_critico = tk.BooleanVar(value=True)
        self._carregar_cfg()

        self.mostrar_login()

    # ── persistência de configurações ────────────────────────────────────────
    def _carregar_cfg(self) -> None:
        if not os.path.exists(CFG_PATH):
            return
        try:
            with open(CFG_PATH, "r", encoding="utf-8") as f:
                d: dict[str, Any] = json.load(f)
            self.cfg_mare_min.set(float(d.get("mare_min", 1.0)))
            self.cfg_vento.set(float(d.get("vento", 60.0)))
            self.cfg_chuva.set(float(d.get("chuva", 50.0)))
            self.cfg_confirmar_politica.set(bool(d.get("confirmar_politica", True)))
            self.cfg_notif_nova.set(bool(d.get("notif_nova", True)))
            self.cfg_notif_sem_espaco.set(bool(d.get("notif_sem_espaco", False)))
            self.cfg_notif_critico.set(bool(d.get("notif_critico", True)))
            pol = str(d.get("politica_padrao", ""))
            if pol in POLITICAS:
                self.politica_ativa = pol
        except (json.JSONDecodeError, KeyError, ValueError, TypeError):
            pass

    def _salvar_cfg(self) -> None:
        dados: dict[str, Any] = {
            "mare_min": round(self.cfg_mare_min.get(), 2),
            "vento": round(self.cfg_vento.get(), 1),
            "chuva": round(self.cfg_chuva.get(), 1),
            "confirmar_politica": self.cfg_confirmar_politica.get(),
            "notif_nova": self.cfg_notif_nova.get(),
            "notif_sem_espaco": self.cfg_notif_sem_espaco.get(),
            "notif_critico": self.cfg_notif_critico.get(),
            "politica_padrao": self.politica_ativa or "",
        }
        with open(CFG_PATH, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)

    def _restaurar_cfg(self) -> None:
        self.cfg_mare_min.set(1.0)
        self.cfg_vento.set(60.0)
        self.cfg_chuva.set(50.0)
        self.cfg_confirmar_politica.set(True)
        self.cfg_notif_nova.set(True)
        self.cfg_notif_sem_espaco.set(False)
        self.cfg_notif_critico.set(True)

    # ── persistência de dados ────────────────────────────────────────────────
    def _salvar(self) -> None:
        Repositorio.salvar(self.fila, self.bercos)

    def limpar(self) -> None:
        for w in self.winfo_children():
            w.destroy()

    # ── tela de login ────────────────────────────────────────────────────────
    def mostrar_login(self) -> None:
        self.limpar()
        self.configure(bg=VERDE_ESCURO)

        # faixas decorativas
        tk.Frame(self, bg="#0f5c0f").place(relx=0, rely=0.72, relwidth=1, relheight=0.28)
        tk.Frame(self, bg="#1e7a1e").place(relx=0, rely=0.68, relwidth=1, relheight=0.06)

        # card branco centralizado
        card = tk.Frame(self, bg="white", relief="flat")
        card.place(relx=0.5, rely=0.46, anchor="center", width=360, height=420)

        # logo
        tk.Label(card, text="S I G A", bg="white", fg=VERDE,
                 font=(FONTE, 22, "bold")).pack(pady=(30, 2))
        tk.Label(card, text="Sistema Inteligente de Gestão de Atracações",
                 bg="white", fg="#888", font=(FONTE, 7),
                 wraplength=270, justify="center").pack(pady=(0, 20))
        tk.Frame(card, bg=BORDA, height=1).pack(fill="x", padx=24, pady=(0, 16))

        # helper de campo — Entry e Combobox com fill="x" para alinhamento uniforme
        def _campo(label: str, var: tk.StringVar, combo: bool = False,
                   values: list[str] | None = None,
                   senha: bool = False) -> tk.Entry | None:
            tk.Label(card, text=label, bg="white", fg="#555",
                     font=(FONTE, 8), anchor="w").pack(padx=24, anchor="w")
            if combo and values:
                ttk.Combobox(card, textvariable=var, values=values,
                             state="readonly",
                             font=(FONTE, 10)).pack(padx=24, pady=(3, 10), fill="x")
                return None
            e = tk.Entry(card, textvariable=var, font=(FONTE, 10),
                         relief="solid", bd=1, show="*" if senha else "")
            e.pack(padx=24, pady=(3, 10), fill="x")
            return e

        v_op    = tk.StringVar()
        v_senha = tk.StringVar()
        v_porto = tk.StringVar(value=PORTOS[0])

        e_op = _campo("Operador", v_op)
        _campo("Senha", v_senha, senha=True)
        _campo("Porto", v_porto, combo=True, values=PORTOS)

        if e_op:
            e_op.focus_set()

        def _validar_campo(nome: str, valor: str) -> str | None:
            """Retorna mensagem de erro ou None se válido."""
            if not valor:
                return f"O campo '{nome}' não pode estar vazio."
            if len(valor) < 3:
                return f"O campo '{nome}' deve ter no mínimo 3 caracteres."
            if len(valor) > 150:
                return f"O campo '{nome}' não pode exceder 150 caracteres."
            return None

        def entrar() -> None:
            op    = v_op.get().strip()
            senha = v_senha.get().strip()
            porto = v_porto.get()

            erros: list[str] = []
            for nome_campo, valor in [("Operador", op), ("Senha", senha)]:
                err = _validar_campo(nome_campo, valor)
                if err:
                    erros.append(err)
            if erros:
                messagebox.showerror("SIGA", "\n".join(erros), parent=card)
                return

            usuarios = _carregar_usuarios()
            usuario = next(
                (u for u in usuarios
                 if u.get("nome", "").lower() == op.lower()
                 and u.get("senha", "") == senha),
                None,
            )
            if not usuario:
                messagebox.showerror(
                    "SIGA", "Usuário ou senha incorretos.", parent=card)
                return
            if usuario.get("porto", "") != porto:
                messagebox.showerror(
                    "SIGA",
                    f"Usuário '{op}' não faz parte deste porto.\n"
                    f"Porto vinculado: {usuario.get('porto', '—')}",
                    parent=card)
                return

            # carrega dados do porto específico
            Repositorio.CAMINHO = Repositorio.caminho_por_porto(porto)
            self.fila, self.bercos = Repositorio.carregar()

            self.operador = op
            self.porto = porto
            self.configure(bg=FUNDO)
            self.mostrar_principal()

        tk.Button(card, text="Entrar", bg=VERDE, fg="white", relief="flat",
                  font=(FONTE, 10, "bold"),
                  activebackground=VERDE_ESCURO, activeforeground="white",
                  command=entrar).pack(padx=24, fill="x", ipady=8, pady=(4, 0))

        self.bind("<Return>", lambda _e: entrar())

        tk.Label(self, text=f"© {datetime.now().year} SIGA · v2.0",
                 bg=VERDE_ESCURO, fg="#aaffaa",
                 font=(FONTE, 7)).place(relx=0.5, rely=0.98, anchor="s")

    # ── estrutura principal ──────────────────────────────────────────────────
    def mostrar_principal(self) -> None:
        self.limpar()
        self.unbind("<Return>")
        self.configure(bg=FUNDO)

        lateral = tk.Frame(self, bg=VERDE, width=190)
        lateral.pack(side="left", fill="y")
        lateral.pack_propagate(False)

        # logo lateral
        tk.Label(lateral, text="S I G A", bg=VERDE, fg="white",
                 font=(FONTE, 13, "bold")).pack(pady=(18, 4))
        tk.Frame(lateral, bg="#2da82d", height=1).pack(fill="x", padx=16, pady=(0, 10))

        self.botoes = {}
        nav: list[tuple[str, Callable[[tk.Frame], None]]] = [
            ("Painel geral",          self.tela_painel),
            ("Política de Atracação", self.tela_politica),
            ("Navios",                self.tela_navios),
            ("Berços",                self.tela_bercos),
            ("Histórico",             self.tela_historico),
            ("Configurações",         self.tela_configuracoes),
        ]
        for nome, tela in nav:
            b = tk.Button(lateral, text=nome, bg=VERDE, fg="white", relief="flat",
                          anchor="w", padx=16, font=(FONTE, 9),
                          activebackground=VERDE_ESCURO, activeforeground="white",
                          command=lambda t=tela, n=nome: self.ir(n, t))  # type: ignore[misc]
            b.pack(fill="x", pady=1)
            self.botoes[nome] = b

        # empurra botão Sair para o rodapé da lateral
        tk.Frame(lateral, bg=VERDE).pack(fill="both", expand=True)
        tk.Frame(lateral, bg="#2da82d", height=1).pack(fill="x", padx=14, pady=(0, 6))
        tk.Button(lateral, text="Sair", bg=VERDE, fg="#ffcccc", relief="flat",
                  anchor="w", padx=16, font=(FONTE, 9),
                  activebackground="#8b1a1a", activeforeground="white",
                  command=self._logout).pack(fill="x", pady=(0, 10))

        # área direita
        direita = tk.Frame(self, bg=FUNDO)
        direita.pack(side="left", fill="both", expand=True)

        topo = tk.Frame(direita, bg=CINZA, height=38)
        topo.pack(fill="x")
        topo.pack_propagate(False)
        self.l_titulo = tk.Label(topo, text="", bg=CINZA,
                                 font=(FONTE, 11, "bold"))
        self.l_titulo.pack(side="left", padx=16, pady=6)

        # lado direito do header: turno + operador
        info_frame = tk.Frame(topo, bg=CINZA)
        info_frame.pack(side="right", padx=14)
        tk.Label(info_frame, text="Turno 14h–22h", bg=CINZA,
                 fg="#666", font=(FONTE, 8)).pack(side="left", padx=(0, 10))
        tk.Label(info_frame,
                 text=f"● {self.operador}  ({self.porto.split()[2] if len(self.porto.split()) > 2 else self.porto})",
                 bg=CINZA, fg=VERDE_ESCURO,
                 font=(FONTE, 8, "bold")).pack(side="left")

        self.conteudo = tk.Frame(direita, bg="white")
        self.conteudo.pack(fill="both", expand=True)

        self.ir("Painel geral", self.tela_painel)
        threading.Thread(target=self.carregar_clima, daemon=True).start()

    def ir(self, nome: str, tela: Callable[[tk.Frame], None]) -> None:
        for n, b in self.botoes.items():
            b.config(bg=VERDE_ESCURO if n == nome else VERDE)
        self.l_titulo.config(text=nome)
        self.tela_atual = (nome, tela)
        self.unbind_all("<MouseWheel>")  # limpa scroll da tela anterior
        for w in self.conteudo.winfo_children():
            w.destroy()
        tela(self.conteudo)

    def _logout(self) -> None:
        self.unbind_all("<MouseWheel>")
        self.operador = ""
        self.porto = ""
        self.fila = []
        self.bercos = []
        self._eventos_api = []
        self.eventos = []
        self.politica_ativa = None
        self.tela_atual = None  # evita que callback da thread de clima chame ir() após logout
        self.mostrar_login()

    def carregar_clima(self) -> None:
        eventos: list[EventoDeRisco] = []
        avisos: list[str] = []
        agora = datetime.now()
        try:
            from ApiClima import ApiClima
            c = ApiClima().condicao_em(agora)
            if c:
                eventos.append(c)
        except Exception as erro:
            avisos.append(f"clima indisponível ({type(erro).__name__})")
        try:
            from ApiMare import ApiMare
            m = JanelaDeMare.da_api(agora, PROFUNDIDADE_CANAL, ApiMare())
            if m:
                eventos.append(m)
        except Exception:
            avisos.append("Maré está adequada.")
        texto = " | ".join([e.descricao() for e in eventos] + avisos) or "Sem dados de clima/maré"
        self.after(0, lambda: self.atualizar_eventos(eventos, texto))

    def _aplicar_cfg_eventos(self) -> None:
        """Reclassifica self._eventos_api usando os limiares do usuário e popula self.eventos.

        cfg_vento  (km/h): vento abaixo deste limiar não bloqueia atracação.
        cfg_chuva  (mm/h): chuva abaixo deste limiar não bloqueia atracação.
        cfg_mare_min (m):  maré abaixo deste limiar eleva classificação para ALTO (alerta),
                           mas o bloqueio efetivo ainda é feito geometricamente por JanelaDeMare.
        """
        vento_ms  = self.cfg_vento.get() / 3.6   # km/h → m/s
        chuva_lim = self.cfg_chuva.get()           # mm/h
        mare_min  = self.cfg_mare_min.get()         # m

        for e in self._eventos_api:
            if isinstance(e, CondicaoClimatica):
                # se abaixo do limiar configurado, cap em MEDIO (não bloqueia)
                if e.get_velocidade_vento() >= vento_ms or e.get_precipitacao() >= chuva_lim:
                    e.set_nivel_de_impacto(NivelDeImpacto.ALTO)
                else:
                    vento_nivel = CondicaoClimatica.classificar_vento(e.get_velocidade_vento())
                    chuva_nivel = CondicaoClimatica.classificar_chuva(e.get_precipitacao())
                    nivel = max(vento_nivel, chuva_nivel)
                    # garante que não bloqueia quando vento/chuva estão dentro do limite
                    if nivel >= NivelDeImpacto.ALTO:
                        nivel = NivelDeImpacto.MEDIO
                    e.set_nivel_de_impacto(nivel)
            elif isinstance(e, JanelaDeMare):
                # eleva classificação para ALTO se maré está abaixo do mínimo configurado
                # (alerta visual); o bloqueio real é geométrico em bloqueia_atracacao
                if e.get_altura_da_mare() < mare_min:
                    e.set_nivel_de_impacto(NivelDeImpacto.ALTO)
                else:
                    e.set_nivel_de_impacto(JanelaDeMare.classificar(e.get_altura_da_mare()))

        self.eventos = list(self._eventos_api)

    def atualizar_eventos(self, eventos: list[EventoDeRisco], texto: str) -> None:
        self._eventos_api = list(eventos)
        self._aplicar_cfg_eventos()
        self.clima_texto.set(texto)
        if self.tela_atual:
            self.ir(*self.tela_atual)

    def politica(self, nome: str | None = None) -> PoliticaDeAtracacao:
        return POLITICAS[nome or self.politica_ativa or "Por ordem de chegada"]

    # ── helpers visuais ──────────────────────────────────────────────────────
    def cartao(self, pai: tk.Frame, titulo: str, valor: int | str) -> tk.Frame:
        f = tk.Frame(pai, bg="white", highlightbackground=VERDE, highlightthickness=2)
        tk.Label(f, text=titulo, bg=VERDE, fg="white",
                 font=(FONTE, 8, "bold")).pack(fill="x")
        tk.Label(f, text=str(valor), bg="white",
                 font=(FONTE, 20)).pack(pady=10)
        return f

    def _barra_botoes(self, pai: tk.Frame,
                      acoes: list[tuple[str, str, Callable[[], None]]]) -> None:
        bts = tk.Frame(pai, bg="white")
        bts.pack(fill="x", padx=16, pady=8)
        for texto, cor, cmd in acoes:
            tk.Button(bts, text=texto, relief="flat", fg=cor,
                      bg=VERDE if cor == "white" else "SystemButtonFace",
                      command=cmd).pack(side="left", padx=(0, 6), ipadx=10)

    def _tree(self, pai: tk.Frame,
              colunas: list[tuple[str, str, int]]) -> ttk.Treeview:
        frame = tk.Frame(pai, bg="white")
        frame.pack(fill="both", expand=True, padx=16, pady=0)
        ids = [c[0] for c in colunas]
        tree = ttk.Treeview(frame, columns=ids, show="headings", selectmode="browse")
        for cid, cab, larg in colunas:
            tree.heading(cid, text=cab)
            tree.column(cid, width=larg, anchor="center")
        sb = ttk.Scrollbar(frame, orient="vertical",
                           command=tree.yview)  # type: ignore[arg-type]
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        return tree

    def _secao(self, pai: tk.Frame, titulo: str) -> tk.Frame:
        """Cabeçalho de seção para tela de configurações."""
        tk.Label(pai, text=titulo, bg="white", fg="#777",
                 font=(FONTE, 7, "bold")).pack(anchor="w", padx=20, pady=(16, 2))
        tk.Frame(pai, bg=BORDA, height=1).pack(fill="x", padx=20, pady=(0, 6))
        corpo = tk.Frame(pai, bg="white")
        corpo.pack(fill="x", padx=20)
        return corpo

    def _linha_slider(self, pai: tk.Frame, titulo: str, var: tk.DoubleVar,
                      de: float, ate: float, unidade: str) -> None:
        """Linha de slider com rótulo e valor."""
        linha = tk.Frame(pai, bg="white")
        linha.pack(fill="x", pady=5)
        tk.Label(linha, text=titulo, bg="white", font=(FONTE, 9),
                 width=28, anchor="w").pack(side="left")
        v_txt = tk.StringVar(value=f"{var.get():.1f} {unidade}")

        def _fmt(_n: str, _i: str, _m: str) -> None:
            v_txt.set(f"{var.get():.1f} {unidade}")

        # limpa traces antigos acumulados de visitas anteriores a esta tela
        for mode, cbname in list(var.trace_info()):
            try:
                var.trace_remove(mode, cbname)
            except Exception:
                pass
        var.trace_add("write", _fmt)
        ttk.Scale(linha, variable=var, from_=de, to=ate,
                  orient="horizontal").pack(side="left", fill="x",
                                            expand=True, padx=(10, 8))
        tk.Label(linha, textvariable=v_txt, bg="white",
                 font=(FONTE, 9), width=10, anchor="e").pack(side="left")

    def _linha_toggle(self, pai: tk.Frame, titulo: str, var: tk.BooleanVar) -> None:
        """Linha de toggle com rótulo."""
        linha = tk.Frame(pai, bg="white")
        linha.pack(fill="x", pady=5)
        tk.Label(linha, text=titulo, bg="white",
                 font=(FONTE, 9)).pack(side="left")
        _Toggle(linha, var).pack(side="right")

    # ── tela: painel ────────────────────────────────────────────────────────
    def tela_painel(self, pai: tk.Frame) -> None:
        pol = self.politica_ativa or "nenhuma"
        tk.Label(pai, text=f"Política ativa: {pol}", bg=VERDE_CLARO,
                 font=(FONTE, 8)).pack(anchor="w", padx=16, pady=(12, 0))
        tk.Label(pai, textvariable=self.clima_texto, bg="white", fg="#666",
                 font=(FONTE, 8)).pack(anchor="w", padx=16)

        linha = tk.Frame(pai, bg="white")
        linha.pack(fill="x", padx=16, pady=12)
        alertas = sum(1 for e in self.eventos
                      if e.esta_ativo() and e.get_nivel_de_impacto() >= NivelDeImpacto.ALTO)
        livres = sum(1 for b in self.bercos if b.get_status() == StatusOperacional.LIVRE)
        cards: list[tuple[str, int | str]] = [
            ("Navios na fila",  len(self.fila)),
            ("Berços livres",   f"{livres} de {len(self.bercos)}"),
            ("Alertas ativos",  alertas),
        ]
        for i, (t, v) in enumerate(cards):
            self.cartao(linha, t, v).grid(row=0, column=i, padx=8, sticky="ew")
            linha.columnconfigure(i, weight=1)

        # ── botões de controle (fixados antes da lista, sempre visíveis) ──────
        prox = self.politica().proxima_atracacao(self.fila, self.bercos, self.eventos)
        navio_p: Navio | None = prox[0] if prox else None
        berco_p: Berco | None = prox[1] if prox else None

        controles = tk.Frame(pai, bg="white")
        controles.pack(fill="x", padx=16, pady=(4, 6))
        if navio_p and berco_p:
            tk.Label(controles,
                     text=f"Próxima: {navio_p.get_nome()} → {berco_p.get_identificador()}",
                     bg="white", font=(FONTE, 9, "bold"),
                     fg=VERDE_ESCURO).pack(side="left")
            tk.Button(controles, text="Atracar", bg=VERDE, fg="white", relief="flat",
                      activebackground=VERDE_ESCURO, activeforeground="white",
                      command=lambda n=navio_p, b=berco_p: self._executar_atracacao(n, b)  # type: ignore[misc]
                      ).pack(side="left", padx=(10, 0), ipadx=6)
        else:
            tk.Label(controles,
                     text="Nenhuma atracação possível no momento",
                     bg="white", font=(FONTE, 9, "bold"),
                     fg=VERDE_ESCURO).pack(side="left")
        tk.Button(controles, text="Avançar turno", bg=VERDE_ESCURO, fg="white",
                  relief="flat", activebackground="#0a4a0a", activeforeground="white",
                  command=self._avancar_turno).pack(side="right", ipadx=6)

        # ── lista de navios rolável ──────────────────────────────────────────
        tk.Label(pai, text="Fila de atracação", bg="white",
                 font=(FONTE, 9, "bold")).pack(anchor="w", padx=16, pady=(2, 2))

        wrapper = tk.Frame(pai, bg="white")
        wrapper.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        canvas = tk.Canvas(wrapper, bg="white", highlightthickness=0)
        sb_fila = ttk.Scrollbar(wrapper, orient="vertical",
                                command=canvas.yview)  # type: ignore[arg-type]
        canvas.configure(yscrollcommand=sb_fila.set)
        sb_fila.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        lista = tk.Frame(canvas, bg="white")
        win_id = canvas.create_window((0, 0), window=lista, anchor="nw")

        def _on_canvas_resize(e: tk.Event[tk.Canvas]) -> None:
            canvas.itemconfig(win_id, width=e.width)

        def _on_lista_resize(_e: tk.Event[tk.Frame]) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", _on_canvas_resize)
        lista.bind("<Configure>", _on_lista_resize)

        def _scroll(e: tk.Event[tk.Misc]) -> None:
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _scroll)

        # pré-computa motivo de bloqueio por navio
        hoje = date.today()
        pol  = self.politica()

        def _motivo_bloqueio(n: Navio) -> str | None:
            """Retorna None se pode atracar, ou texto explicando por quê não pode."""
            if not any(b.aceita_navio(n) for b in self.bercos):
                return "sem berço"
            if pol.bloqueios(n, self.eventos, hoje):
                return "risco bloqueado"
            return None

        for n in pol.ordenar_fila(self.fila, self.eventos):
            st      = self.gerenciador.status_navio(n, self.eventos)
            motivo  = _motivo_bloqueio(n)
            pode    = motivo is None
            is_prox = navio_p is not None and n is navio_p

            r_bg = VERDE_CLARO if is_prox else (CINZA if pode else "#ebebeb")
            r = tk.Frame(lista, bg=r_bg)
            r.pack(fill="x", pady=2)

            dot_cor = COR_STATUS[st] if pode else "#b0b0b0"
            tk.Label(r, text="●", fg=dot_cor, bg=r_bg).pack(side="left", padx=6)

            txt_cor = "black" if pode else "#a0a0a0"
            tk.Label(r,
                     text=f"{n.get_nome()} · {n.get_carga_atual().get_tipo()} · calado {n.get_calado()} m",
                     bg=r_bg, fg=txt_cor, font=(FONTE, 9)).pack(side="left")

            if is_prox:
                tk.Label(r, text="→ próxima", fg=VERDE_ESCURO, bg=r_bg,
                         font=(FONTE, 7, "bold")).pack(side="right", padx=(0, 6))
            elif motivo:
                tk.Label(r, text=motivo, fg="#a0a0a0", bg=r_bg,
                         font=(FONTE, 7)).pack(side="right", padx=(0, 6))

            tk.Label(r, text=st, fg=dot_cor, bg=r_bg,
                     font=(FONTE, 8, "bold")).pack(side="right", padx=8)

    def _executar_atracacao(self, navio: Navio, berco: Berco) -> None:
        self.gerenciador.atracar(navio, berco, self.fila)
        self._salvar()
        if self.tela_atual:
            self.ir(*self.tela_atual)

    def _avancar_turno(self) -> None:
        n = self.gerenciador.avancar_turno(self.bercos)
        self._salvar()
        if self.tela_atual:
            self.ir(*self.tela_atual)
        messagebox.showinfo("SIGA", f"Turno avançado: {n} berço(s) liberado(s).")

    # ── tela: navios (CRUD) ──────────────────────────────────────────────────
    def tela_navios(self, pai: tk.Frame) -> None:
        tk.Label(pai, text="Fila de navios", bg="white",
                 font=(FONTE, 9, "bold")).pack(anchor="w", padx=16, pady=(12, 4))
        cols: list[tuple[str, str, int]] = [
            ("nome",       "Nome",        140),
            ("calado",     "Calado (m)",   80),
            ("tamanho",    "Tamanho (m)",  90),
            ("tipo",       "Tipo",        110),
            ("volume",     "Volume",       80),
            ("origem",     "Origem",       90),
            ("destino",    "Destino",      90),
            ("capacidade", "Capacidade",   90),
        ]
        tree = self._tree(pai, cols)

        def preencher() -> None:
            tree.delete(*tree.get_children())
            for n in self.fila:
                c = n.get_carga_atual()
                tree.insert("", "end", values=(
                    n.get_nome(), n.get_calado(), n.get_tamanho(),
                    c.get_tipo(), c.get_volume(), c.get_origem(),
                    c.get_destino(), n.get_capacidade(),
                ))

        preencher()

        def novo() -> None:
            n = self._dialogo_navio()
            if n:
                self.fila.append(n)
                self._salvar()
                preencher()

        def editar() -> None:
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("SIGA", "Selecione um navio para editar.")
                return
            idx = tree.index(sel[0])
            n = self._dialogo_navio(self.fila[idx])
            if n:
                self.fila[idx] = n
                self._salvar()
                preencher()

        def excluir() -> None:
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("SIGA", "Selecione um navio para excluir.")
                return
            idx = tree.index(sel[0])
            nome = self.fila[idx].get_nome()
            if messagebox.askyesno("SIGA", f"Excluir o navio '{nome}'?"):
                self.fila.pop(idx)
                self._salvar()
                preencher()

        self._barra_botoes(pai, [
            ("Novo",    "white",   novo),
            ("Editar",  "black",   editar),
            ("Excluir", "#c0392b", excluir),
        ])

    # ── tela: berços (CRUD) ──────────────────────────────────────────────────
    def tela_bercos(self, pai: tk.Frame) -> None:
        tk.Label(pai, text="Berços", bg="white",
                 font=(FONTE, 9, "bold")).pack(anchor="w", padx=16, pady=(12, 4))
        cols: list[tuple[str, str, int]] = [
            ("id",         "Identificador",  110),
            ("capacidade", "Capacidade (m)", 120),
            ("tipos",      "Tipos aceitos",  240),
            ("status",     "Status",         100),
        ]
        tree = self._tree(pai, cols)

        def preencher() -> None:
            tree.delete(*tree.get_children())
            for b in self.bercos:
                tree.insert("", "end", values=(
                    b.get_identificador(),
                    b.get_capacidade(),
                    ", ".join(b.get_tipos_carga_aceita()),
                    b.get_status().value,
                ))

        preencher()

        def novo() -> None:
            b = self._dialogo_berco()
            if b:
                self.bercos.append(b)
                self._salvar()
                preencher()

        def editar() -> None:
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("SIGA", "Selecione um berço para editar.")
                return
            idx = tree.index(sel[0])
            old = self.bercos[idx]
            if old.get_status() == StatusOperacional.OCUPADO:
                messagebox.showerror(
                    "SIGA",
                    f"O berço '{old.get_identificador()}' está ocupado.\nLibere-o antes de editar.")
                return
            b = self._dialogo_berco(old)
            if b:
                self.bercos[idx] = b
                self._salvar()
                preencher()

        def excluir() -> None:
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("SIGA", "Selecione um berço para excluir.")
                return
            idx = tree.index(sel[0])
            old = self.bercos[idx]
            if old.get_status() == StatusOperacional.OCUPADO:
                messagebox.showerror(
                    "SIGA",
                    f"O berço '{old.get_identificador()}' está ocupado e não pode ser excluído.")
                return
            if messagebox.askyesno("SIGA", f"Excluir o berço '{old.get_identificador()}'?"):
                self.bercos.pop(idx)
                self._salvar()
                preencher()

        self._barra_botoes(pai, [
            ("Novo",    "white",   novo),
            ("Editar",  "black",   editar),
            ("Excluir", "#c0392b", excluir),
        ])

    # ── tela: histórico ──────────────────────────────────────────────────────
    def tela_historico(self, pai: tk.Frame) -> None:
        tk.Label(pai, text="Histórico de operações", bg="white",
                 font=(FONTE, 9, "bold")).pack(anchor="w", padx=16, pady=(12, 4))
        cols: list[tuple[str, str, int]] = [
            ("timestamp", "Data/Hora", 150),
            ("tipo",      "Operação",  100),
            ("navio",     "Navio",     200),
            ("berco",     "Berço",     100),
        ]
        tree = self._tree(pai, cols)
        for reg in reversed(self.historico.get_registros()):
            tree.insert("", "end", values=(
                reg.timestamp, reg.tipo, reg.navio_nome, reg.berco_id))

        def limpar() -> None:
            if messagebox.askyesno("SIGA", "Limpar todo o histórico?"):
                self.historico.limpar()
                tree.delete(*tree.get_children())

        self._barra_botoes(pai, [("Limpar histórico", "#c0392b", limpar)])

    # ── tela: configurações ──────────────────────────────────────────────────
    def tela_configuracoes(self, pai: tk.Frame) -> None:
        tk.Label(pai, text="Configurações do sistema", bg="white",
                 font=(FONTE, 9, "bold")).pack(anchor="w", padx=20, pady=(14, 0))

        # ── Limites de alerta ────────────────────────────────────────────────
        s1 = self._secao(pai, "LIMITES DE ALERTA")
        self._linha_slider(s1, "Altura mínima de maré",
                           self.cfg_mare_min, 0.0, 5.0, "m")
        self._linha_slider(s1, "Vento crítico",
                           self.cfg_vento, 20.0, 100.0, "km/h")
        self._linha_slider(s1, "Chuva intensa",
                           self.cfg_chuva, 10.0, 100.0, "mm/h")

        # ── Política de atracação ────────────────────────────────────────────
        s2 = self._secao(pai, "POLÍTICA DE ATRACAÇÃO")
        linha_pol = tk.Frame(s2, bg="white")
        linha_pol.pack(fill="x", pady=5)
        tk.Label(linha_pol, text="Política padrão", bg="white",
                 font=(FONTE, 9), width=28, anchor="w").pack(side="left")
        v_pol = tk.StringVar(value=self.politica_ativa or list(POLITICAS.keys())[2])
        ttk.Combobox(linha_pol, textvariable=v_pol,
                     values=list(POLITICAS.keys()),
                     state="readonly", width=28).pack(side="left")

        self._linha_toggle(s2, "Pedir confirmação ao trocar de política",
                           self.cfg_confirmar_politica)

        # ── Notificações ─────────────────────────────────────────────────────
        s3 = self._secao(pai, "NOTIFICAÇÕES")
        self._linha_toggle(s3, "Nova atracação disponível", self.cfg_notif_nova)
        self._linha_toggle(s3, "Sem espaço em dois dias", self.cfg_notif_sem_espaco)
        self._linha_toggle(s3, "Alerta crítico", self.cfg_notif_critico)

        # ── Botões ───────────────────────────────────────────────────────────
        def salvar() -> None:
            pol_nova = v_pol.get()
            if pol_nova in POLITICAS:
                self.politica_ativa = pol_nova
            self._salvar_cfg()
            self._aplicar_cfg_eventos()
            messagebox.showinfo("SIGA", "Configurações salvas com sucesso.")

        def restaurar() -> None:
            if messagebox.askyesno("SIGA", "Restaurar todas as configurações para o padrão?"):
                self._restaurar_cfg()
                self.politica_ativa = None
                v_pol.set(list(POLITICAS.keys())[2])
                self._aplicar_cfg_eventos()
                self._salvar_cfg()

        bts = tk.Frame(pai, bg="white")
        bts.pack(anchor="w", padx=20, pady=16)
        tk.Button(bts, text="Salvar informações", bg=VERDE, fg="white",
                  relief="flat", activebackground=VERDE_ESCURO, activeforeground="white",
                  command=salvar).pack(side="left", ipadx=10, padx=(0, 8))
        tk.Button(bts, text="Restaurar padrões", relief="flat",
                  command=restaurar).pack(side="left", ipadx=10)

    # ── diálogos ─────────────────────────────────────────────────────────────
    def _dialogo_navio(self, existente: Navio | None = None) -> Navio | None:
        d = tk.Toplevel(self)
        d.title("Novo Navio" if existente is None else "Editar Navio")
        d.resizable(False, False)
        d.configure(bg="white")
        d.grab_set()
        d.focus_set()

        ex_c = existente.get_carga_atual() if existente else None
        v_nome    = tk.StringVar(value=existente.get_nome()            if existente else "")
        v_calado  = tk.StringVar(value=str(existente.get_calado())     if existente else "")
        v_tamanho = tk.StringVar(value=str(existente.get_tamanho())    if existente else "")
        v_cap     = tk.StringVar(value=str(existente.get_capacidade()) if existente else "")
        v_tipo    = tk.StringVar(value=ex_c.get_tipo()   if ex_c else TIPOS_CARGA[0])
        v_volume  = tk.StringVar(value=str(ex_c.get_volume())  if ex_c else "")
        v_origem  = tk.StringVar(value=ex_c.get_origem()  if ex_c else "")
        v_destino = tk.StringVar(value=ex_c.get_destino() if ex_c else "")

        campos: list[tuple[str, tk.StringVar, bool]] = [
            ("Nome",          v_nome,    False),
            ("Calado (m)",    v_calado,  False),
            ("Tamanho (m)",   v_tamanho, False),
            ("Capacidade",    v_cap,     False),
            ("Tipo de Carga", v_tipo,    True),
            ("Volume",        v_volume,  False),
            ("Origem",        v_origem,  False),
            ("Destino",       v_destino, False),
        ]
        for i, (lbl, var, combo) in enumerate(campos):
            tk.Label(d, text=lbl, bg="white", font=(FONTE, 9),
                     anchor="e").grid(row=i, column=0, padx=(14, 6), pady=4, sticky="e")
            if combo:
                ttk.Combobox(d, textvariable=var, values=TIPOS_CARGA,
                             state="readonly", width=22).grid(
                    row=i, column=1, padx=(0, 14), pady=4, sticky="w")
            else:
                tk.Entry(d, textvariable=var, width=24,
                         font=(FONTE, 9)).grid(row=i, column=1, padx=(0, 14), pady=4)

        resultado: list[Navio | None] = [None]

        def confirmar() -> None:
            nome    = v_nome.get().strip()
            origem  = v_origem.get().strip()
            destino = v_destino.get().strip()
            if not nome:
                messagebox.showerror("SIGA", "Nome é obrigatório.", parent=d)
                return
            try:
                calado  = float(v_calado.get())
                tamanho = float(v_tamanho.get())
                cap     = float(v_cap.get())
                volume  = float(v_volume.get())
            except ValueError:
                messagebox.showerror(
                    "SIGA", "Calado, tamanho, capacidade e volume devem ser números.", parent=d)
                return
            if any(x <= 0 for x in (calado, tamanho, cap, volume)):
                messagebox.showerror("SIGA", "Valores numéricos devem ser positivos.", parent=d)
                return
            resultado[0] = Navio(nome, calado, tamanho,
                                 Carga(v_tipo.get(), volume, origem, destino), cap)
            d.destroy()

        bts = tk.Frame(d, bg="white")
        bts.grid(row=len(campos), column=0, columnspan=2, pady=(8, 14))
        tk.Button(bts, text="Cancelar", relief="flat",
                  command=d.destroy).pack(side="left", padx=6)
        tk.Button(bts, text="Salvar", bg=VERDE, fg="white", relief="flat",
                  activebackground=VERDE_ESCURO, activeforeground="white",
                  command=confirmar).pack(side="left", padx=6, ipadx=10)

        d.bind("<Return>", lambda _e: confirmar())
        d.bind("<Escape>", lambda _e: d.destroy())
        self.wait_window(d)
        return resultado[0]

    def _dialogo_berco(self, existente: Berco | None = None) -> Berco | None:
        d = tk.Toplevel(self)
        d.title("Novo Berço" if existente is None else "Editar Berço")
        d.resizable(False, False)
        d.configure(bg="white")
        d.grab_set()
        d.focus_set()

        ex_tipos = existente.get_tipos_carga_aceita() if existente else []
        v_id  = tk.StringVar(value=existente.get_identificador() if existente else "")
        v_cap = tk.StringVar(value=str(existente.get_capacidade()) if existente else "")
        checks: dict[str, tk.BooleanVar] = {
            t: tk.BooleanVar(value=t in ex_tipos) for t in TIPOS_CARGA
        }

        tk.Label(d, text="Identificador", bg="white",
                 font=(FONTE, 9)).grid(row=0, column=0, padx=(14, 6), pady=6, sticky="e")
        tk.Entry(d, textvariable=v_id, width=20,
                 font=(FONTE, 9)).grid(row=0, column=1, padx=(0, 14), pady=6)

        tk.Label(d, text="Capacidade (m)", bg="white",
                 font=(FONTE, 9)).grid(row=1, column=0, padx=(14, 6), pady=6, sticky="e")
        tk.Entry(d, textvariable=v_cap, width=20,
                 font=(FONTE, 9)).grid(row=1, column=1, padx=(0, 14), pady=6)

        tk.Label(d, text="Tipos aceitos:", bg="white",
                 font=(FONTE, 9)).grid(row=2, column=0, padx=(14, 6), pady=(10, 2), sticky="ne")
        frame_checks = tk.Frame(d, bg="white")
        frame_checks.grid(row=2, column=1, padx=(0, 14), pady=(10, 2), sticky="w")
        for t, bv in checks.items():
            tk.Checkbutton(frame_checks, text=t, variable=bv, bg="white",
                           activebackground="white",
                           font=(FONTE, 9)).pack(anchor="w")

        resultado: list[Berco | None] = [None]

        def confirmar() -> None:
            ident = v_id.get().strip()
            if not ident:
                messagebox.showerror("SIGA", "Identificador é obrigatório.", parent=d)
                return
            try:
                cap = float(v_cap.get())
            except ValueError:
                messagebox.showerror("SIGA", "Capacidade deve ser um número.", parent=d)
                return
            if cap <= 0:
                messagebox.showerror("SIGA", "Capacidade deve ser positiva.", parent=d)
                return
            tipos = [t for t, bv in checks.items() if bv.get()]
            if not tipos:
                messagebox.showerror("SIGA", "Selecione pelo menos um tipo de carga.", parent=d)
                return
            resultado[0] = Berco(ident, cap, tipos)
            d.destroy()

        bts = tk.Frame(d, bg="white")
        bts.grid(row=3, column=0, columnspan=2, pady=(8, 14))
        tk.Button(bts, text="Cancelar", relief="flat",
                  command=d.destroy).pack(side="left", padx=6)
        tk.Button(bts, text="Salvar", bg=VERDE, fg="white", relief="flat",
                  activebackground=VERDE_ESCURO, activeforeground="white",
                  command=confirmar).pack(side="left", padx=6, ipadx=10)

        d.bind("<Return>", lambda _e: confirmar())
        d.bind("<Escape>", lambda _e: d.destroy())
        self.wait_window(d)
        return resultado[0]

    # ── tela: política ───────────────────────────────────────────────────────
    def tela_politica(self, pai: tk.Frame) -> None:
        tk.Label(pai, text="Escolha a Política de Atracação:", bg="white",
                 font=(FONTE, 9, "bold")).pack(anchor="w", padx=16, pady=(14, 6))
        self.escolhida = tk.StringVar(value=self.politica_ativa or "")
        cartoes = tk.Frame(pai, bg="white")
        cartoes.pack(fill="x", padx=16)
        self.widgets_politica = {}
        for i, (nome, pol) in enumerate(POLITICAS.items()):
            c = tk.Frame(cartoes, bg="white", highlightbackground=VERDE,
                         highlightthickness=2, cursor="hand2")
            c.grid(row=0, column=i, padx=6, sticky="nsew")
            cartoes.columnconfigure(i, weight=1)
            l1 = tk.Label(c, text=nome, bg="white", font=(FONTE, 9, "bold"))
            l2 = tk.Label(c, text=pol.get_descricao(), bg="white", font=(FONTE, 8),
                          wraplength=190, justify="left")
            l1.pack(anchor="w", padx=8, pady=(8, 2))
            l2.pack(anchor="w", padx=8, pady=(0, 8))
            for w in (c, l1, l2):
                w.bind("<Button-1>", lambda e, n=nome: self.selecionar_politica(n))  # type: ignore[misc]
            self.widgets_politica[nome] = (c, l1, l2)

        # botão Confirmar fixado abaixo dos cards (sempre visível)
        tk.Button(pai, text="Confirmar política", bg=VERDE, fg="white", relief="flat",
                  activebackground=VERDE_ESCURO, activeforeground="white",
                  command=self.confirmar_politica).pack(anchor="e", padx=16, pady=(14, 6), ipadx=10)

        tk.Label(pai, text="Prévia da fila com esta política:", bg="white",
                 font=(FONTE, 9, "bold")).pack(anchor="w", padx=16, pady=(0, 4))

        # prévia rolável
        wrapper_prev = tk.Frame(pai, bg="white")
        wrapper_prev.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        canvas_prev = tk.Canvas(wrapper_prev, bg="white", highlightthickness=0)
        sb_prev = ttk.Scrollbar(wrapper_prev, orient="vertical",
                                command=canvas_prev.yview)  # type: ignore[arg-type]
        canvas_prev.configure(yscrollcommand=sb_prev.set)
        sb_prev.pack(side="right", fill="y")
        canvas_prev.pack(side="left", fill="both", expand=True)

        self.previa = tk.Frame(canvas_prev, bg="white")
        win_prev = canvas_prev.create_window((0, 0), window=self.previa, anchor="nw")

        def _resize_prev(e: tk.Event[tk.Canvas]) -> None:
            canvas_prev.itemconfig(win_prev, width=e.width)

        def _scroll_prev(_e: tk.Event[tk.Frame]) -> None:
            canvas_prev.configure(scrollregion=canvas_prev.bbox("all"))

        def _wheel_prev(e: tk.Event[tk.Misc]) -> None:
            canvas_prev.yview_scroll(int(-1 * (e.delta / 120)), "units")

        canvas_prev.bind("<Configure>", _resize_prev)
        self.previa.bind("<Configure>", _scroll_prev)
        canvas_prev.bind_all("<MouseWheel>", _wheel_prev)

        self.selecionar_politica(self.politica_ativa)

    def selecionar_politica(self, nome: str | None) -> None:
        self.escolhida.set(nome or "")
        for n, (c, l1, l2) in self.widgets_politica.items():
            sel = n == nome
            for w in (c, l1, l2):
                w.config(bg=VERDE if sel else "white")
            l1.config(fg="white" if sel else "black")
            l2.config(fg="white" if sel else "black")
        for w in self.previa.winfo_children():
            w.destroy()
        if nome:
            for pos, n in enumerate(
                    self.politica(nome).ordenar_fila(self.fila, self.eventos), 1):
                tk.Label(self.previa,
                         text=f"{pos}. {n.get_nome()} — {n.get_carga_atual().get_tipo()} (calado {n.get_calado()} m)",
                         bg=CINZA, anchor="w", font=(FONTE, 9)).pack(fill="x", pady=2)

    def confirmar_politica(self) -> None:
        nova = self.escolhida.get()
        if not nova:
            messagebox.showinfo(
                "SIGA",
                "Nenhuma política foi escolhida, faça uma escolha entre as três disponíveis na tela.")
            return
        if (self.cfg_confirmar_politica.get()
                and self.politica_ativa
                and self.politica_ativa != nova):
            if not messagebox.askyesno(
                    "SIGA", f"Trocar política de '{self.politica_ativa}' para '{nova}'?"):
                return
        self.politica_ativa = nova
        messagebox.showinfo("SIGA", f"Política aplicada: {self.politica_ativa}")


if __name__ == "__main__":
    App().mainloop()
