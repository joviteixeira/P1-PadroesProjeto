from __future__ import annotations
import os, time
from typing import Dict, Any, List

from app.core.session import get_session
from app.core.users import FACTORIES, User
from app.challenges.challenge import QuizChallenge
from app.challenges.scoring import CompositeStrategy, DifficultyStrategy, AccuracyStrategy, TimeStrategy
from app.challenges.observers import ConsoleNotifier, AuditObserver
from app.gamification.points import PointsEngine
from app.gamification.achievements import Medal, MedalSet
from app.history.commands import History, AwardPointsCommand, AwardMedalCommand, QuizAttemptCommand
from app.reports.facade import ReportsFacade
from app.utils.persistence import JsonStore
from app.utils.audit import AuditLog

class ConsoleApp:
    def __init__(self):
        self.session = get_session()
        self.users: Dict[str, User] = {}
        self.challenges: Dict[str, QuizChallenge] = {}
        self.points_engine = PointsEngine()
        self.points_engine.attach(ConsoleNotifier())
        self.history = History()
        self.reports = ReportsFacade()
        self.store = JsonStore(os.path.join(os.getcwd(), "data.json"))
        self._init_demo_data()
        self._init_achievements()

    def _init_demo_data(self):
        # demo challenge
        self.challenges["quiz1"] = QuizChallenge(
            id="quiz1", title="Quiz Padrões de Projeto", difficulty=2,
            questions=[
                {"q": "Qual padrão garante uma única instância?", "options": ["Factory", "Singleton", "Observer"], "correct_index": 1},
                {"q": "Qual padrão notifica dependentes?", "options": ["Observer", "Adapter", "Facade"], "correct_index": 0},
            ]
        )

    def _init_achievements(self):
        # Composite hierarchy
        self.ach_tree = MedalSet("Conquistas")
        iniciante = MedalSet("Iniciante")
        iniciante.add(Medal("Iniciante 100+"))
        intermediario = MedalSet("Intermediário")
        intermediario.add(Medal("Intermediário 500+"))
        self.ach_tree.add(iniciante)
        self.ach_tree.add(intermediario)

    def run(self):
        while True:
            print("\n=== Plataforma Gamificada (Console) ===")
            print("Usuário:", self.session.current_user.username if self.session.is_authenticated() else "(não logado)")
            print("1) Login\n2) Cadastrar usuário\n3) Listar usuários\n4) Responder desafio\n5) Exportar relatórios\n6) Leaderboard (Adapter)\n7) Histórico/Undo\n8) Conquistas\n9) Salvar/Carregar\n0) Sair")
            op = input("> ").strip()
            if op == "1": self.menu_login()
            elif op == "2": self.menu_cadastrar()
            elif op == "3": self.menu_listar()
            elif op == "4": self.menu_responder()
            elif op == "5": self.menu_exportar()
            elif op == "6": self.menu_leaderboard()
            elif op == "7": self.menu_history()
            elif op == "8": self.menu_conquistas()
            elif op == "9": self.menu_persistencia()
            elif op == "0": break

    def menu_login(self):
        u = input("Usuário: ").strip()
        if u in self.users:
            self.session.login(u, self.users[u].role)
            print("Logado como:", u, self.users[u].role)
        else:
            print("Usuário não encontrado.")

    def menu_cadastrar(self):
        u = input("Novo usuário: ").strip()
        role = input("Tipo (ALUNO/PROFESSOR/VISITANTE): ").strip().upper()
        if role not in FACTORIES:
            print("Tipo inválido."); return
        self.users[u] = FACTORIES[role].create(u)
        print("Cadastrado:", self.users[u])

    def menu_listar(self):
        for u, obj in self.users.items():
            print(f"- {u} | {obj.role} | pontos={obj.points} | lvl={obj.level} | medals={obj.medals}")

    def menu_responder(self):
        if not self.session.is_authenticated():
            print("Faça login primeiro."); return
        ch = self.challenges.get("quiz1")
        if not ch:
            print("Sem desafios."); return
        print("Respondendo:", ch.title)
        answers: List[int] = []
        start = time.time()
        for i, q in enumerate(ch.questions):
            print(f"Q{i+1}: {q['q']}")
            for j, opt in enumerate(q['options']):
                print(f"  {j}) {opt}")
            ans = int(input("Sua resposta (número): ").strip() or "-1")
            answers.append(ans)
        elapsed = time.time() - start
        result = ch.evaluate(answers)
        context = {
            "difficulty": ch.difficulty,
            "accuracy": result["accuracy"],
            "time_sec": elapsed,
        }
        strat = CompositeStrategy(DifficultyStrategy(), AccuracyStrategy(), TimeStrategy())
        raw_pts = strat.score(context)
        print(f"Pontuação base calculada: {raw_pts}")
        dbl = input("Aplicar Double XP? (s/n): ").strip().lower() == 's'
        streak = int(input("Dias de streak (0 para nenhum): ").strip() or "0")
        # usar PointsEngine (Observer + Decorator)
        earned = self.points_engine.award(self.users[self.session.current_user.username], raw_pts, double_xp=dbl, streak_days=streak)
        print("Pontos recebidos:", earned)
        # registrar comandos no histórico
        self.history.push_and_exec(AwardPointsCommand(self.users[self.session.current_user.username], 0))  # marcador
        print("Resultado:", result)

    def menu_exportar(self):
        rows = [{
            "username": u.username,
            "role": u.role,
            "points": u.points,
            "level": u.level,
            "medals": ",".join(u.medals),
        } for u in self.users.values()]
        base = os.path.join(os.getcwd(), "desempenho")
        paths = self.reports.export_all(base, rows)
        for k, v in paths.items():
            print(f"{k.upper()} => {v}")

    def menu_leaderboard(self):
        top = self.reports.leaderboard(10)
        print("TOP (externo adaptado):")
        for i, row in enumerate(top, 1):
            print(f"{i:02d}. {row['username']} - {row['points']} pts")

    def menu_history(self):
        print("1) Desfazer última ação  |  2) Premiar medalha (comando)  |  3) Ver audit log (últimos 20)")
        op = input("> ").strip()
        if op == "1":
            print(self.history.undo_last())
        elif op == "2":
            if not self.session.is_authenticated():
                print("Faça login primeiro."); return
            medal = input("Medalha: ").strip()
            cmd = AwardMedalCommand(self.users[self.session.current_user.username], medal)
            self.history.push_and_exec(cmd)
            print("Medalha concedida (pode desfazer em 'Desfazer').")

    def menu_conquistas(self):
        print(f"Conjunto: {self.ach_tree.name()}  | total de medalhas: {self.ach_tree.total_medals()}" )
        for m in self.ach_tree.list_medals():
            print("-", m)

    def menu_persistencia(self):
        print("1) Salvar  |  2) Carregar")
        op = input("> ").strip()
        if op == "1":
            data = {u: {"role": obj.role, "points": obj.points, "level": obj.level, "medals": obj.medals} for u, obj in self.users.items()}
            self.store.save(data); print("OK salvo.")
        else:
            raw = self.store.load()
            for u, info in raw.items():
                factory = FACTORIES.get(info.get("role", "ALUNO"))
                if factory:
                    self.users[u] = factory.create(u)
                    self.users[u].points = info.get("points", 0)
                    self.users[u].level = info.get("level", 1)
                    self.users[u].medals = info.get("medals", [])
            print("OK carregado.")
