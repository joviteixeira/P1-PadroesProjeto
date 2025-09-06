from __future__ import annotations
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog  # filedialog pode ser útil depois
from typing import Dict, List

from app.core.session import get_session
from app.core.users import FACTORIES, User
from app.challenges.challenge import QuizChallenge
from app.challenges.scoring import CompositeStrategy, DifficultyStrategy, AccuracyStrategy, TimeStrategy
from app.challenges.observers import ConsoleNotifier, AuditObserver
from app.gamification.points import PointsEngine
from app.gamification.achievements import Medal, MedalSet
from app.history.commands import History, AwardMedalCommand, QuizAttemptCommand
from app.reports.facade import ReportsFacade
from app.utils.persistence import JsonStore
from app.utils.audit import AuditLog


class AppGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Plataforma Gamificada - GUI")
        self.geometry("980x640")

        # Estado / serviços
        self.session = get_session()
        self.users: Dict[str, User] = {}
        self.challenges: Dict[str, QuizChallenge] = {}
        self.points_engine = PointsEngine()
        self.points_engine.attach(ConsoleNotifier())
        self.audit = AuditLog(os.path.join(os.getcwd(), "audit.log"))
        self.points_engine.attach(AuditObserver(self.audit))
        self.history = History()
        self.reports = ReportsFacade()
        self.store = JsonStore(os.path.join(os.getcwd(), "data.json"))
        self._init_demo_data()
        self._init_achievements()

        # UI
        self._build_menu()
        self._build_header()
        self._build_tabs()
        self._refresh_user_table()
        self._refresh_achievements()
        self._refresh_audit()

    # ---------------- State bootstrap ----------------
    def _init_demo_data(self):
        # Quiz avançado com pesos por questão
        questions = [
            {"q": "Qual padrão garante uma única instância do objeto?",
             "options": ["Factory", "Singleton", "Observer", "Builder"], "correct_index": 1, "weight": 1.0},
            {"q": "Qual padrão notifica múltiplos interessados quando o estado muda?",
             "options": ["Observer", "Adapter", "Decorator", "Facade"], "correct_index": 0, "weight": 1.2},
            {"q": "Qual padrão converte a interface de uma classe em outra esperada pelo cliente?",
             "options": ["Adapter", "Strategy", "Composite", "Proxy"], "correct_index": 0, "weight": 1.0},
            {"q": "Qual padrão encapsula algoritmos intercambiáveis?",
             "options": ["Strategy", "Decorator", "Factory Method", "Prototype"], "correct_index": 0, "weight": 1.3},
            {"q": "Qual padrão fornece uma interface unificada para um subsistema?",
             "options": ["Bridge", "Facade", "Flyweight", "Mediator"], "correct_index": 1, "weight": 0.8},
            {"q": "Qual padrão adiciona responsabilidades dinamicamente a objetos?",
             "options": ["Decorator", "Observer", "Chain of Responsibility", "State"], "correct_index": 0, "weight": 1.4},
            {"q": "Qual padrão compõe objetos em estruturas de árvore (parte–todo)?",
             "options": ["Composite", "Prototype", "Builder", "Iterator"], "correct_index": 0, "weight": 1.2},
            {"q": "Qual padrão separa abstração da implementação?",
             "options": ["Bridge", "Facade", "Adapter", "Proxy"], "correct_index": 0, "weight": 1.1},
            {"q": "Qual padrão fornece um substituto/representante para controlar acesso a um objeto?",
             "options": ["Proxy", "Mediator", "Visitor", "Memento"], "correct_index": 0, "weight": 1.0},
            {"q": "Qual padrão define uma família de algoritmos e os torna intercambiáveis?",
             "options": ["Strategy", "State", "Template Method", "Command"], "correct_index": 0, "weight": 1.0},
            {"q": "Qual padrão registra comandos e permite desfazer operações?",
             "options": ["Command", "Observer", "Interpreter", "Visitor"], "correct_index": 0, "weight": 0.9},
            {"q": "Qual padrão reduz o custo de muitos objetos semelhantes compartilhando estado?",
             "options": ["Flyweight", "Prototype", "Builder", "Singleton"], "correct_index": 0, "weight": 1.5},
        ]

        self.challenges["quiz1"] = QuizChallenge(
            id="quiz1",
            title="Quiz Padrões de Projeto (Avançado)",
            difficulty=3,
            questions=questions
        )

    def _init_achievements(self):
        self.ach_tree = MedalSet("Conquistas")
        iniciante = MedalSet("Iniciante"); iniciante.add(Medal("Iniciante 100+"))
        intermediario = MedalSet("Intermediário"); intermediario.add(Medal("Intermediário 500+"))
        self.ach_tree.add(iniciante); self.ach_tree.add(intermediario)

    # ---------------- UI building ----------------
    def _build_menu(self):
        menubar = tk.Menu(self)
        # Arquivo
        m_file = tk.Menu(menubar, tearoff=0)
        m_file.add_command(label="Salvar", command=self._save_data)
        m_file.add_command(label="Carregar", command=self._load_data)
        m_file.add_separator()
        m_file.add_command(label="Exportar Relatórios", command=self._export_reports)
        m_file.add_separator()
        m_file.add_command(label="Sair", command=self.destroy)
        menubar.add_cascade(label="Arquivo", menu=m_file)

        # Ações
        m_actions = tk.Menu(menubar, tearoff=0)
        m_actions.add_command(label="Desfazer (Undo)", command=self._undo_last)
        menubar.add_cascade(label="Ações", menu=m_actions)

        self.config(menu=menubar)

    def _build_header(self):
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="x")

        self.lbl_user = ttk.Label(frame, text="(não logado)")
        self.lbl_user.pack(side="right")

        btn_login = ttk.Button(frame, text="Login", command=self._open_login_dialog)
        btn_login.pack(side="left", padx=5)

        btn_register = ttk.Button(frame, text="Cadastrar Usuário", command=self._open_register_dialog)
        btn_register.pack(side="left", padx=5)

    def _build_tabs(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab Usuários
        self.tab_users = ttk.Frame(nb); nb.add(self.tab_users, text="Usuários")
        self._build_users_tab(self.tab_users)

        # Tab Desafio
        self.tab_quiz = ttk.Frame(nb); nb.add(self.tab_quiz, text="Desafio (Quiz)")
        self._build_quiz_tab(self.tab_quiz)

        # Tab Leaderboard
        self.tab_lb = ttk.Frame(nb); nb.add(self.tab_lb, text="Leaderboard (Adapter)")
        self._build_lb_tab(self.tab_lb)

        # Tab Conquistas
        self.tab_ach = ttk.Frame(nb); nb.add(self.tab_ach, text="Conquistas")
        self._build_ach_tab(self.tab_ach)

        # Tab Auditoria
        self.tab_audit = ttk.Frame(nb); nb.add(self.tab_audit, text="Audit Log")
        self._build_audit_tab(self.tab_audit)

    # ----- Users Tab -----
    def _build_users_tab(self, parent):
        cols = ("username", "role", "points", "level", "medals")
        self.tree_users = ttk.Treeview(parent, columns=cols, show="headings", height=16)
        for c in cols:
            self.tree_users.heading(c, text=c.capitalize())
            self.tree_users.column(c, width=150 if c != "medals" else 300, anchor="w")
        self.tree_users.pack(fill="both", expand=True)

        btns = ttk.Frame(parent); btns.pack(fill="x", pady=6)
        ttk.Button(btns, text="Exportar Relatórios", command=self._export_reports).pack(side="left", padx=5)
        ttk.Button(btns, text="Salvar", command=self._save_data).pack(side="left", padx=5)
        ttk.Button(btns, text="Carregar", command=self._load_data).pack(side="left", padx=5)

    def _refresh_user_table(self):
        for i in self.tree_users.get_children():
            self.tree_users.delete(i)
        for u in self.users.values():
            self.tree_users.insert("", "end", values=(u.username, u.role, u.points, u.level, ",".join(u.medals)))

    # ----- Quiz Tab -----
    def _build_quiz_tab(self, parent):
        self.quiz_desc = ttk.Label(parent, text="Quiz de demonstração sobre Padrões de Projeto.")
        self.quiz_desc.pack(anchor="w", padx=5, pady=(10, 5))

        # Options (double xp / streak)
        opts = ttk.Frame(parent); opts.pack(fill="x", padx=5, pady=5)
        self.var_double = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts, text="Double XP", variable=self.var_double).pack(side="left", padx=5)
        ttk.Label(opts, text="Streak (dias):").pack(side="left")
        self.var_streak = tk.IntVar(value=0)
        ttk.Spinbox(opts, from_=0, to=30, textvariable=self.var_streak, width=6).pack(side="left", padx=5)

        self.quiz_frame = ttk.Labelframe(parent, text="Perguntas")
        self.quiz_frame.pack(fill="x", padx=5, pady=10)

        # render question widgets dynamically
        self._render_quiz_questions()

        ttk.Button(parent, text="Enviar Respostas", command=self._submit_quiz).pack(anchor="e", padx=10, pady=10)

        self.lbl_quiz_result = ttk.Label(parent, text="Resultado: -")
        self.lbl_quiz_result.pack(anchor="w", padx=10, pady=(0, 10))

    def _render_quiz_questions(self):
        for child in self.quiz_frame.winfo_children():
            child.destroy()
        ch = self.challenges.get("quiz1")
        if not ch:
            ttk.Label(self.quiz_frame, text="Nenhum desafio disponível.").pack(anchor="w", padx=10, pady=8)
            return
        self.quiz_vars: List[tk.IntVar] = []
        for i, q in enumerate(ch.questions):
            box = ttk.Frame(self.quiz_frame); box.pack(fill="x", padx=10, pady=6)
            ttk.Label(box, text=f"Q{i+1}: {q['q']}").pack(anchor="w")
            var = tk.IntVar(value=-1)
            self.quiz_vars.append(var)
            for j, opt in enumerate(q["options"]):
                ttk.Radiobutton(box, text=opt, value=j, variable=var).pack(anchor="w", padx=12)

    def _submit_quiz(self):
        if not self.session.is_authenticated():
            messagebox.showwarning("Login", "Faça login para responder o desafio.")
            return
        ch = self.challenges.get("quiz1")
        if not ch:
            return
        answers = [v.get() for v in self.quiz_vars]
        result = ch.evaluate(answers)

        # Build score using Strategy
        import time
        start = time.time(); time.sleep(0.05)  # simula um pequeno tempo de resposta
        elapsed = time.time() - start
        strat = CompositeStrategy(DifficultyStrategy(), AccuracyStrategy(), TimeStrategy())
        raw_pts = strat.score({"difficulty": ch.difficulty, "accuracy": result["accuracy"], "time_sec": elapsed})

        user = self.users[self.session.current_user.username]
        dbl = self.var_double.get()
        streak = int(self.var_streak.get())

        # Log de alto nível
        self.audit.add("QUIZ_ANSWERED", user.username, {"challenge_id": ch.id, "accuracy": result["accuracy"], "time_sec": int(elapsed)})

        # Executa via Command (permite UNDO completo)
        cmd = QuizAttemptCommand(user, self.points_engine, raw_pts, dbl, streak)
        self.history.push_and_exec(cmd)

        self.lbl_quiz_result.config(
            text=f"Resultado: acertos={result['correct']}/{result['total']} | pontos +{cmd.last_awarded} (raw={raw_pts})"
        )
        self._refresh_user_table()
        self._refresh_lb()            # <- atualiza leaderboard após pontuar
        self._refresh_audit()
        messagebox.showinfo("Quiz", "Respostas enviadas e pontuação aplicada!")

    # ----- Leaderboard Tab -----
    def _build_lb_tab(self, parent):
        # Fonte selector
        src_frame = ttk.Frame(parent)
        src_frame.pack(fill="x", padx=5, pady=(8, 4))
        ttk.Label(src_frame, text="Fonte:").pack(side="left")
        self.var_lb_source = tk.StringVar(value="Interna")
        cb = ttk.Combobox(src_frame, textvariable=self.var_lb_source,
                          values=["Interna", "Externa"], state="readonly", width=12)
        cb.pack(side="left", padx=6)
        cb.bind("<<ComboboxSelected>>", lambda e: self._refresh_lb())

        cols = ("pos", "username", "points")
        self.tree_lb = ttk.Treeview(parent, columns=cols, show="headings", height=16)
        for c in cols:
            self.tree_lb.heading(c, text=c.capitalize())
            self.tree_lb.column(c, width=120, anchor="center" if c == "pos" else "w")
        self.tree_lb.pack(fill="both", expand=True, padx=5, pady=5)

        ttk.Button(parent, text="Atualizar Leaderboard", command=self._refresh_lb)\
            .pack(anchor="e", padx=10, pady=8)

    def _internal_lb(self):
        rows = sorted(self.users.values(), key=lambda u: u.points, reverse=True)
        return [{"username": u.username, "points": u.points} for u in rows]

    def _refresh_lb(self):
        for i in self.tree_lb.get_children():
            self.tree_lb.delete(i)
        rows = self._internal_lb() if self.var_lb_source.get() == "Interna" else self.reports.leaderboard(10)
        for i, row in enumerate(rows, 1):
            self.tree_lb.insert("", "end", values=(i, row["username"], row["points"]))

    # ----- Achievements Tab -----
    def _build_ach_tab(self, parent):
        self.lbl_ach_summary = ttk.Label(parent, text="Conquistas: -")
        self.lbl_ach_summary.pack(anchor="w", padx=8, pady=6)

        self.lst_ach = tk.Listbox(parent, height=10)
        self.lst_ach.pack(fill="both", expand=True, padx=8, pady=6)

    def _refresh_achievements(self):
        self.lbl_ach_summary.config(
            text=f"Conjunto: {self.ach_tree.name()} | total de medalhas: {self.ach_tree.total_medals()}"
        )
        self.lst_ach.delete(0, tk.END)
        for m in self.ach_tree.list_medals():
            self.lst_ach.insert(tk.END, f"- {m}")

    # ----- Audit Tab -----
    def _build_audit_tab(self, parent):
        self.txt_audit = tk.Text(parent, height=20)
        self.txt_audit.pack(fill="both", expand=True, padx=8, pady=8)

        btns = ttk.Frame(parent); btns.pack(fill="x", pady=6)
        ttk.Button(btns, text="Atualizar", command=self._refresh_audit).pack(side="left", padx=5)

    def _refresh_audit(self):
        self.txt_audit.delete("1.0", tk.END)
        for rec in self.audit.tail(200):
            self.txt_audit.insert(tk.END, f"{rec['ts']} | {rec.get('username','-')} | {rec['event']} | {rec.get('meta', {})}\n")

    # ---------------- Dialogs/actions ----------------
    def _open_login_dialog(self):
        dlg = tk.Toplevel(self); dlg.title("Login"); dlg.geometry("320x150"); dlg.transient(self); dlg.grab_set()
        ttk.Label(dlg, text="Usuário:").pack(anchor="w", padx=10, pady=(10, 4))
        var_user = tk.StringVar(); ent = ttk.Entry(dlg, textvariable=var_user); ent.pack(fill="x", padx=10)
        ent.focus_set()

        def do_login():
            u = var_user.get().strip()
            if u not in self.users:
                messagebox.showerror("Login", "Usuário não encontrado."); return
            self.session.login(u, self.users[u].role)
            self.lbl_user.config(text=f"{u} ({self.users[u].role})")
            dlg.destroy()

        ttk.Button(dlg, text="Entrar", command=do_login).pack(pady=10)

    def _open_register_dialog(self):
        dlg = tk.Toplevel(self); dlg.title("Cadastrar Usuário"); dlg.geometry("360x220"); dlg.transient(self); dlg.grab_set()
        ttk.Label(dlg, text="Usuário:").pack(anchor="w", padx=10, pady=(10, 4))
        var_user = tk.StringVar(); ttk.Entry(dlg, textvariable=var_user).pack(fill="x", padx=10)

        ttk.Label(dlg, text="Tipo:").pack(anchor="w", padx=10, pady=(10, 4))
        var_role = tk.StringVar(value="ALUNO")
        cb = ttk.Combobox(dlg, textvariable=var_role, values=["ALUNO", "PROFESSOR", "VISITANTE"], state="readonly")
        cb.pack(fill="x", padx=10)

        def do_register():
            u = var_user.get().strip(); role = var_role.get().strip().upper()
            if not u:
                messagebox.showerror("Cadastro", "Informe o nome do usuário."); return
            if role not in FACTORIES:
                messagebox.showerror("Cadastro", "Tipo inválido."); return
            self.users[u] = FACTORIES[role].create(u)
            self._refresh_user_table()
            dlg.destroy()

        ttk.Button(dlg, text="Cadastrar", command=do_register).pack(pady=12)

    def _save_data(self):
        data = {u: {"role": obj.role, "points": obj.points, "level": obj.level, "medals": obj.medals}
                for u, obj in self.users.items()}
        self.store.save(data)
        messagebox.showinfo("Salvar", "Dados salvos em data.json.")

    def _load_data(self):
        raw = self.store.load()
        for u, info in raw.items():
            factory = FACTORIES.get(info.get("role", "ALUNO"))
            if factory:
                self.users[u] = factory.create(u)
                self.users[u].points = info.get("points", 0)
                self.users[u].level = info.get("level", 1)
                self.users[u].medals = info.get("medals", [])
        self._refresh_user_table()
        messagebox.showinfo("Carregar", "Dados carregados de data.json.")

    def _export_reports(self):
        rows = [{
            "username": u.username,
            "role": u.role,
            "points": u.points,
            "level": u.level,
            "medals": ",".join(u.medals),
        } for u in self.users.values()]
        base = os.path.join(os.getcwd(), "desempenho")
        paths = self.reports.export_all(base, rows)
        messagebox.showinfo("Exportação", f"CSV: {paths['csv']}\nJSON: {paths['json']}\nPDF: {paths['pdf']}")

    def _undo_last(self):
        msg = self.history.undo_last()
        if msg is None:
            msg = "Nada para desfazer."
        self._refresh_user_table()
        messagebox.showinfo("Undo", msg)


def run():
    app = AppGUI()
    app.mainloop()
