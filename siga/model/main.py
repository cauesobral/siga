import os
import sys
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

# os módulos do projeto usam imports simples (from EventoDeRisco import ...)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "model"))

VERDE, VERDE_ESCURO, FUNDO, CINZA = "#1a8a1a", "#126b12", "#f2f2f2", "#dcdcdc"
FONTE = "Helvetica"

# Dados de demonstração (trocar pelas classes Navio/Berco quando estiverem prontas)
FILA = [
    {"nome": "MSC Aurora", "carga": "Contêineres", "calado": 12.5, "status": "Normal"},
    {"nome": "Petro Santos", "carga": "Petróleo", "calado": 13.8, "status": "Atenção"},
    {"nome": "Graneleiro Sul", "carga": "Granel", "calado": 11.2, "status": "Risco Alto"},
    {"nome": "Atlântico I", "carga": "Contêineres", "calado": 10.9, "status": "Atenção"},
]
PRIORIDADE_CARGA = {"Petróleo": 0, "Granel": 1, "Contêineres": 2}
POLITICAS = {
    "Por maré": "Prioriza navios de acordo com janelas de maré segura.",
    "Por prioridade de carga": "Prioriza cargas críticas, ex.: petróleo.",
    "Por ordem de chegada": "Mantém a fila na ordem de chegada.",
}
COR_STATUS = {"Normal": "#1a8a1a", "Atenção": "#d4a000", "Risco Alto": "#c0392b"}


def ordenar_fila(politica):
    if politica == "Por maré":
        return sorted(FILA, key=lambda n: n["calado"])
    if politica == "Por prioridade de carga":
        return sorted(FILA, key=lambda n: PRIORIDADE_CARGA.get(n["carga"], 9))
    return list(FILA)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SIGA - Sistema Inteligente de Gestão de Atracações")
        self.geometry("1000x620")
        self.minsize(900, 560)
        self.configure(bg=FUNDO)
        self.usuario = ""
        self.politica_ativa = None
        self.clima_texto = tk.StringVar(value="Clima: carregando...")
        self.mostrar_login()

    def limpar(self):
        for w in self.winfo_children():
            w.destroy()

    # ---------------- login ----------------
    def mostrar_login(self):
        self.limpar()
        fundo = tk.Frame(self, bg="#2b4a5e")
        fundo.pack(fill="both", expand=True)
        cartao = tk.Frame(fundo, bg="white")
        cartao.place(relx=0.5, rely=0.5, anchor="center", width=560, height=300)
        esq = tk.Frame(cartao, bg=VERDE, width=200)
        esq.pack(side="left", fill="y")
        esq.pack_propagate(False)
        tk.Label(esq, text="SIGA", bg=VERDE, fg="white", font=(FONTE, 16, "bold")).pack(pady=(30, 10))
        tk.Label(esq, text="Sem atrasos, sem surpresas:\nacompanhe a fila de atracação\ncom segurança.",
                 bg=VERDE, fg="white", font=(FONTE, 9), justify="left").pack(padx=14)
        dir_ = tk.Frame(cartao, bg="white")
        dir_.pack(side="left", fill="both", expand=True, padx=24, pady=20)
        tk.Label(dir_, text="Entrar no SIGA", bg="white", font=(FONTE, 14, "bold")).pack(pady=(0, 12))
        tk.Label(dir_, text="usuário", bg="white", fg=VERDE, font=(FONTE, 8)).pack(anchor="w")
        self.e_user = ttk.Entry(dir_)
        self.e_user.pack(fill="x", pady=(0, 8))
        tk.Label(dir_, text="senha", bg="white", fg=VERDE, font=(FONTE, 8)).pack(anchor="w")
        self.e_senha = ttk.Entry(dir_, show="•")
        self.e_senha.pack(fill="x")
        self.v_ver = tk.BooleanVar(value=False)
        tk.Checkbutton(dir_, text="mostrar senha", variable=self.v_ver, bg="white",
                       font=(FONTE, 8), command=lambda: self.e_senha.config(
                           show="" if self.v_ver.get() else "•")).pack(anchor="w")
        self.l_erro = tk.Label(dir_, text="", bg="white", fg="#c0392b", font=(FONTE, 8))
        self.l_erro.pack()
        tk.Button(dir_, text="entrar", bg=VERDE, fg="white", relief="flat",
                  command=self.entrar).pack(pady=4, ipadx=14)
        self.e_user.focus_set()
        self.bind("<Return>", lambda e: self.entrar())

    def entrar(self):
        usuario, senha = self.e_user.get().strip(), self.e_senha.get()
        # Autenticação de demonstração: só exige preenchimento.
        if not usuario or not senha:
            self.l_erro.config(text="Preencha usuário e senha.")
            return
        self.usuario = usuario
        self.unbind("<Return>")


    # ---------------- estrutura principal ----------------
    def mostrar_principal(self):
        self.limpar()
        lateral = tk.Frame(self, bg=VERDE, width=170)
        lateral.pack(side="left", fill="y")
        lateral.pack_propagate(False)
        tk.Label(lateral, text="S I G A", bg=VERDE, fg="white", font=(FONTE, 12, "bold")).pack(pady=18)
        self.botoes = {}
        for nome, tela in (("Painel geral", self.tela_painel), ("Política de Atracação", self.tela_politica),
                           ("Histórico", self.tela_historico), ("Configurações", self.tela_config)):
            b = tk.Button(lateral, text=nome, bg=VERDE, fg="white", relief="flat", anchor="w",
                          padx=14, font=(FONTE, 9), activebackground=VERDE_ESCURO,
                          activeforeground="white", command=lambda t=tela, n=nome: self.ir(n, t))
            b.pack(fill="x", pady=2)
            self.botoes[nome] = b
        tk.Button(lateral, text="Sair", bg=VERDE, fg="white", relief="flat", anchor="w", padx=14,
                  command=self.mostrar_login).pack(side="bottom", fill="x", pady=10)
        direita = tk.Frame(self, bg=FUNDO)
        direita.pack(side="left", fill="both", expand=True)
        topo = tk.Frame(direita, bg=CINZA, height=36)
        topo.pack(fill="x")
        self.l_titulo = tk.Label(topo, text="", bg=CINZA, font=(FONTE, 11, "bold"))
        self.l_titulo.pack(side="left", padx=14)
        tk.Label(topo, text=f"Turno 14h-22h · operador {self.usuario}", bg=CINZA,
                 font=(FONTE, 8)).pack(side="right", padx=14)
        self.conteudo = tk.Frame(direita, bg="white")
        self.conteudo.pack(fill="both", expand=True)
        self.ir("Painel geral", self.tela_painel)
        threading.Thread(target=self.carregar_clima, daemon=True).start()

    def ir(self, nome, tela):
        for n, b in self.botoes.items():
            b.config(bg=VERDE_ESCURO if n == nome else VERDE)
        self.l_titulo.config(text=nome)
        for w in self.conteudo.winfo_children():
            w.destroy()
        tela(self.conteudo)

    def carregar_clima(self):
        try:
            from ApiClima import ApiClima
            c = ApiClima().condicao_em(datetime.now())
            texto = "Clima: " + c.descricao() if c else "Clima: sem dado para esta hora"
        except Exception as erro:  # sem internet, biblioteca ausente, etc.
            texto = f"Clima indisponível ({type(erro).__name__})"
        self.after(0, lambda: self.clima_texto.set(texto))

    # ---------------- telas ----------------
    def cartao(self, pai, titulo, valor):
        f = tk.Frame(pai, bg="white", highlightbackground=VERDE, highlightthickness=2)
        tk.Label(f, text=titulo, bg=VERDE, fg="white", font=(FONTE, 8, "bold")).pack(fill="x")
        tk.Label(f, text=valor, bg="white", font=(FONTE, 20)).pack(pady=10)
        return f

    def tela_painel(self, pai):
        pol = self.politica_ativa or "nenhuma"
        tk.Label(pai, text=f"Política ativa: {pol}", bg="#d5ecd5", font=(FONTE, 8)).pack(anchor="w", padx=16, pady=(12, 0))
        tk.Label(pai, textvariable=self.clima_texto, bg="white", fg="#555", font=(FONTE, 8)).pack(anchor="w", padx=16)
        linha = tk.Frame(pai, bg="white")
        linha.pack(fill="x", padx=16, pady=12)
        alertas = sum(1 for n in FILA if n["status"] == "Risco Alto")
        for i, (t, v) in enumerate((("Navios na fila", len(FILA)), ("Berços livres", "3 de 9"),
                                    ("Alertas ativos", alertas))):
            self.cartao(linha, t, v).grid(row=0, column=i, padx=8, sticky="ew")
            linha.columnconfigure(i, weight=1)
        tk.Label(pai, text="Fila de atracação", bg="white", font=(FONTE, 9, "bold")).pack(anchor="w", padx=16)
        for n in ordenar_fila(self.politica_ativa or "Por ordem de chegada"):
            r = tk.Frame(pai, bg=CINZA)
            r.pack(fill="x", padx=16, pady=3)
            tk.Label(r, text="●", fg=COR_STATUS[n["status"]], bg=CINZA).pack(side="left", padx=6)
            tk.Label(r, text=f'{n["nome"]} · {n["carga"]} · calado {n["calado"]} m', bg=CINZA,
                     font=(FONTE, 9)).pack(side="left")
            tk.Label(r, text=n["status"], fg=COR_STATUS[n["status"]], bg=CINZA,
                     font=(FONTE, 8, "bold")).pack(side="right", padx=8)

    def tela_politica(self, pai):
        tk.Label(pai, text="Escolha a Política de Atracação:", bg="white", font=(FONTE, 9, "bold")).pack(anchor="w", padx=16, pady=(14, 6))
        self.escolhida = tk.StringVar(value=self.politica_ativa or "")
        cartoes = tk.Frame(pai, bg="white")
        cartoes.pack(fill="x", padx=16)
        self.widgets_politica = {}
        for i, (nome, desc) in enumerate(POLITICAS.items()):
            c = tk.Frame(cartoes, bg="white", highlightbackground=VERDE, highlightthickness=2, cursor="hand2")
            c.grid(row=0, column=i, padx=6, sticky="nsew")
            cartoes.columnconfigure(i, weight=1)
            l1 = tk.Label(c, text=nome, bg="white", font=(FONTE, 9, "bold"))
            l2 = tk.Label(c, text=desc, bg="white", font=(FONTE, 8), wraplength=190, justify="left")
            l1.pack(anchor="w", padx=8, pady=(8, 2))
            l2.pack(anchor="w", padx=8, pady=(0, 8))
            for w in (c, l1, l2):
                w.bind("<Button-1>", lambda e, n=nome: self.selecionar_politica(n))
            self.widgets_politica[nome] = (c, l1, l2)
        tk.Label(pai, text="Prévia da fila com esta política:", bg="white", font=(FONTE, 9, "bold")).pack(anchor="w", padx=16, pady=(14, 4))
        self.previa = tk.Frame(pai, bg="white")
        self.previa.pack(fill="x", padx=16)
        tk.Button(pai, text="Confirmar", bg=VERDE, fg="white", relief="flat",
                  command=self.confirmar_politica).pack(anchor="e", padx=16, pady=14, ipadx=10)
        self.selecionar_politica(self.politica_ativa)

    def selecionar_politica(self, nome):
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
            for pos, n in enumerate(ordenar_fila(nome), 1):
                tk.Label(self.previa, text=f'{pos}. {n["nome"]} — {n["carga"]} (calado {n["calado"]} m)',
                         bg=CINZA, anchor="w", font=(FONTE, 9)).pack(fill="x", pady=2)

    def confirmar_politica(self):
        if not self.escolhida.get():
            messagebox.showinfo("SIGA", "Nenhuma política foi escolhida, faça uma escolha entre as três disponíveis na tela.")
            return
        self.politica_ativa = self.escolhida.get()
        messagebox.showinfo("SIGA", f"Política aplicada: {self.politica_ativa}")

    def tela_historico(self, pai):
        tk.Label(pai, text="Tempo médio de espera por política (horas)", bg="white", font=(FONTE, 9, "bold")).pack(anchor="w", padx=16, pady=(14, 4))
        dados = [("Maré", 3.2), ("Carga", 4.5), ("Chegada", 5.1)]  # demonstração
        cv = tk.Canvas(pai, width=520, height=220, bg="white", highlightthickness=0)
        cv.pack(anchor="w", padx=16)
        for i, (nome, v) in enumerate(dados):
            x = 40 + i * 110
            cv.create_rectangle(x, 190 - v * 30, x + 60, 190, fill="#2f6fed", outline="")
            cv.create_text(x + 30, 180 - v * 30, text=str(v), font=(FONTE, 9))
            cv.create_text(x + 30, 204, text=nome, font=(FONTE, 8))
        cv.create_arc(380, 40, 500, 160, start=0, extent=200, fill="#2ecc40", outline="white")
        cv.create_arc(380, 40, 500, 160, start=200, extent=160, fill="#2f6fed", outline="white")
        tk.Label(pai, text="Dados de demonstração — ligar ao registro real de atracações.", bg="white", fg="#777", font=(FONTE, 8)).pack(anchor="w", padx=16)

    def tela_config(self, pai):
        def slider(rotulo, de, ate, ini, unid):
            f = tk.Frame(pai, bg="white")
            f.pack(fill="x", padx=16, pady=4)
            tk.Label(f, text=rotulo, bg="white", font=(FONTE, 9), width=24, anchor="w").pack(side="left")
            v = tk.DoubleVar(value=ini)
            tk.Label(f, textvariable=v, bg="white", width=6).pack(side="right")
            ttk.Scale(f, from_=de, to=ate, variable=v, command=lambda x, v=v: v.set(round(float(x), 1))).pack(side="right", fill="x", expand=True, padx=8)
            tk.Label(f, text=unid, bg="white").pack(side="right")
            return v
        tk.Label(pai, text="Limiares de alerta", bg="white", font=(FONTE, 10, "bold")).pack(anchor="w", padx=16, pady=(12, 0))
        self.cfg = {"mare": slider("Altura mínima de maré", 0, 3, 0.6, "m"),
                    "vento": slider("Vento crítico", 0, 25, 11, "m/s"),
                    "chuva": slider("Chuva intensa", 0, 60, 7.6, "mm/h")}
        tk.Label(pai, text="Notificações e acessibilidade", bg="white", font=(FONTE, 10, "bold")).pack(anchor="w", padx=16, pady=(12, 0))
        for txt in ("Banner discreto para alertas", "Som ao entrar em risco alto", "Alto contraste"):
            tk.Checkbutton(pai, text=txt, bg="white", font=(FONTE, 9)).pack(anchor="w", padx=16)
        botoes = tk.Frame(pai, bg="white")
        botoes.pack(anchor="w", padx=16, pady=14)
        tk.Button(botoes, text="Salvar Alterações", bg=VERDE, fg="white", relief="flat",
                  command=lambda: messagebox.showinfo("SIGA", "Configurações salvas.")).pack(side="left", padx=(0, 8))
        tk.Button(botoes, text="Restaurar Padrões", relief="flat",
                  command=self.restaurar).pack(side="left")

    def restaurar(self):
        if messagebox.askyesno("SIGA", "Isso restaurará todas as configurações salvas, tem certeza disso?"):
            for chave, valor in (("mare", 0.6), ("vento", 11), ("chuva", 7.6)):
                self.cfg[chave].set(valor)


if __name__ == "__main__":
    App().mainloop()
