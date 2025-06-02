import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw
import sqlite3
from datetime import datetime
import os
import shutil
import sys

class AcademicSystem:
    def __init__(self):
        self.db_file = "academic.db"
        self.initialize_db()
        self.root = tk.Tk()
        self.setup_ui()
        self.activities_dir = "activities"
        self.submissions_dir = "submissions"
        
        # Criar diretórios se não existirem
        os.makedirs(self.activities_dir, exist_ok=True)
        os.makedirs(self.submissions_dir, exist_ok=True)
    
    def initialize_db(self):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Tabela de usuários
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    user_type TEXT NOT NULL,
                    is_approved INTEGER DEFAULT 0,
                    approved_by TEXT,
                    registered_at TEXT
                )
            """)
            
            # Tabela de alunos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    username TEXT PRIMARY KEY,
                    matricula TEXT NOT NULL,
                    nome TEXT NOT NULL,
                    data_nascimento TEXT,
                    cpf TEXT,
                    curso TEXT,
                    email TEXT,
                    telefone TEXT,
                    endereco TEXT,
                    progresso REAL DEFAULT 0,
                    FOREIGN KEY (username) REFERENCES users(username)
                )
            """)
            
            # Tabela de atividades
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    deadline TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    FOREIGN KEY (created_by) REFERENCES users(username)
                )
            """)
            
            # Tabela de submissões
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    activity_id INTEGER NOT NULL,
                    student_username TEXT NOT NULL,
                    submission_date TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    grade REAL,
                    feedback TEXT,
                    FOREIGN KEY (activity_id) REFERENCES activities(id),
                    FOREIGN KEY (student_username) REFERENCES users(username)
                )
            """)
            
            # Criar admin padrão se não existir
            cursor.execute("SELECT * FROM users WHERE username='admin'")
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO users VALUES (
                        'admin', 'admin123', 'admin', 1, 'system', ?
                    )
                """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
            
            conn.commit()
    
    def setup_ui(self):
        self.root.title("Sistema Acadêmico")
        self.root.geometry("500x650")
        self.root.resizable(False, False)
        
        # Configurar logo
        self.setup_logo()
        
        # Frame principal
        main_frame = tk.Frame(self.root)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        
        # Campos de login
        tk.Label(main_frame, text="Usuário:").pack(anchor="w")
        self.username_entry = tk.Entry(main_frame, font=("Helvetica", 12))
        self.username_entry.pack(fill=tk.X, pady=5, ipady=5)
        
        tk.Label(main_frame, text="Senha:").pack(anchor="w")
        self.password_entry = tk.Entry(main_frame, show="•", font=("Helvetica", 12))
        self.password_entry.pack(fill=tk.X, pady=5, ipady=5)
        
        # Botão de login
        tk.Button(
            main_frame,
            text="Entrar",
            command=self.login,
            bg="#4CAF50",
            fg="white",
            font=("Helvetica", 12),
            pady=10
        ).pack(fill=tk.X, pady=20)
        
        # Botões de registro
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        
        tk.Button(
            btn_frame,
            text="Registrar Professor",
            command=lambda: RegisterScreen(self, "professor"),
            font=("Helvetica", 10)
        ).pack(side=tk.LEFT, expand=True, padx=5)
        
        tk.Button(
            btn_frame,
            text="Registrar Aluno",
            command=lambda: RegisterScreen(self, "aluno"),
            font=("Helvetica", 10)
        ).pack(side=tk.LEFT, expand=True, padx=5)
    
    def setup_logo(self):
        try:
            # Caminho base diferente quando executando como script vs executável
            if getattr(sys, 'frozen', False):
                # Modo executável - usa sys._MEIPASS
                base_path = sys._MEIPASS
            else:
                # Modo desenvolvimento - usa o diretório do script
                base_path = os.path.dirname(os.path.abspath(__file__))
        
            # Caminho para a logo
            logo_path = os.path.join(base_path, 'vclass', 'logo.png')
        
            img = Image.open(logo_path)
            img = img.resize((200, 200), Image.Resampling.LANCZOS)
            self.logo = ImageTk.PhotoImage(img)
            logo_label = tk.Label(self.root, image=self.logo)
            logo_label.pack(pady=20)
        
        except Exception as e:
            print(f"Erro ao carregar logo: {str(e)}")
            # Fallback - cria uma logo simples
            img = Image.new('RGB', (200, 200), color='lightgray')
            draw = ImageDraw.Draw(img)
            draw.text((50, 90), "LOGO AQUI", fill="black")
            self.logo = ImageTk.PhotoImage(img)
            logo_label = tk.Label(self.root, image=self.logo)
            logo_label.pack(pady=20)
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM users 
                WHERE username=? AND password=? AND is_approved=1
            """, (username, password))
            
            user = cursor.fetchone()
            
            if user:
                messagebox.showinfo("Sucesso", f"Bem-vindo, {username}!")
                self.root.withdraw()
                
                if user["user_type"] == "admin":
                    AdminPanel(self)
                elif user["user_type"] == "professor":
                    ProfessorMainPanel(self, username)
                elif user["user_type"] == "aluno":
                    StudentPanel(self, username)
            else:
                messagebox.showerror("Erro", "Credenciais inválidas ou conta não aprovada!")
    
    def register_user(self, username, password, user_type):
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (username, password, user_type, registered_at)
                    VALUES (?, ?, ?, ?)
                """, (username, password, user_type, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                return True, "Solicitação enviada com sucesso!"
        except sqlite3.IntegrityError:
            return False, "Usuário já existe!"
    
    def register_student(self, student_data):
        try:
            username = f"aluno_{student_data['matricula']}"
        
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
            
                # Primeiro cria o usuário
                cursor.execute("""
                    INSERT INTO users (username, password, user_type, registered_at)
                    VALUES (?, ?, ?, ?)
                """, (username, student_data["cpf"], "aluno", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
                # Depois insere os dados do aluno (agora com as colunas explicitas)
                cursor.execute("""
                    INSERT INTO students (
                        username, matricula, nome, data_nascimento, cpf, 
                        curso, email, telefone, endereco
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                username,
                    student_data["matricula"],
                    student_data["nome"],
                    student_data.get("data_nascimento", ""),
                    student_data.get("cpf", ""),
                    student_data.get("curso", ""),
                    student_data.get("email", ""),
                    student_data.get("telefone", ""),
                    student_data.get("endereco", "")
                ))
            
                conn.commit()
                return True, f"Registro de aluno {student_data['nome']} solicitado com sucesso!"
        except sqlite3.IntegrityError:
            return False, "Matrícula já cadastrada!"
    
    def get_pending_students(self):
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.* FROM students s
                JOIN users u ON s.username = u.username
                WHERE u.is_approved = 0
            """)
            return cursor.fetchall()
    
    def approve_student(self, username, approved_by):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users 
                SET is_approved=1, approved_by=?
                WHERE username=?
            """, (approved_by, username))
            conn.commit()
            return True, f"Aluno {username} aprovado com sucesso!"
    
    def create_activity(self, title, description, deadline, professor_username):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO activities (title, description, deadline, created_at, created_by)
                VALUES (?, ?, ?, ?, ?)
            """, (title, description, deadline, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), professor_username))
            conn.commit()
            return True, "Atividade criada com sucesso!"
    
    def get_activities_for_student(self, student_username):
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.*, 
                       CASE WHEN s.id IS NOT NULL THEN 1 ELSE 0 END as submitted,
                       s.grade,
                       s.feedback
                FROM activities a
                LEFT JOIN submissions s ON a.id = s.activity_id AND s.student_username = ?
                ORDER BY a.deadline
            """, (student_username,))
            return cursor.fetchall()
    
    def submit_activity(self, activity_id, student_username, file_path):
        # Copiar arquivo para o diretório de submissões
        submission_dir = os.path.join(self.submissions_dir, f"activity_{activity_id}")
        os.makedirs(submission_dir, exist_ok=True)
        
        filename = f"{student_username}_{os.path.basename(file_path)}"
        dest_path = os.path.join(submission_dir, filename)
        shutil.copyfile(file_path, dest_path)
        
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            
            # Verificar se já existe uma submissão
            cursor.execute("""
                SELECT id FROM submissions 
                WHERE activity_id=? AND student_username=?
            """, (activity_id, student_username))
            
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE submissions
                    SET submission_date=?, file_path=?
                    WHERE activity_id=? AND student_username=?
                """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), dest_path, activity_id, student_username))
            else:
                cursor.execute("""
                    INSERT INTO submissions (activity_id, student_username, submission_date, file_path)
                    VALUES (?, ?, ?, ?)
                """, (activity_id, student_username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), dest_path))
            
            # Atualizar progresso do aluno
            cursor.execute("""
                UPDATE students
                SET progresso = (
                    SELECT COUNT(DISTINCT activity_id) * 100.0 / 
                           (SELECT COUNT(*) FROM activities)
                    FROM submissions
                    WHERE student_username = ?
                )
                WHERE username = ?
            """, (student_username, student_username))
            
            conn.commit()
            return True, "Atividade entregue com sucesso!"
    
    def get_all_students(self):
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.* FROM students s
                JOIN users u ON s.username = u.username
                WHERE u.is_approved = 1
                ORDER BY s.nome
            """)
            return cursor.fetchall()
    
    def get_student_submissions(self, student_username):
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.title, a.deadline, s.submission_date, s.file_path, s.grade, s.feedback
                FROM submissions s
                JOIN activities a ON s.activity_id = a.id
                WHERE s.student_username = ?
                ORDER BY a.deadline
            """, (student_username,))
            return cursor.fetchall()
    
    def get_class_progress(self):
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.nome, s.matricula, s.progresso,
                       (SELECT COUNT(*) FROM submissions WHERE student_username = s.username) as entregas,
                       (SELECT COUNT(*) FROM activities) as total_atividades
                FROM students s
                JOIN users u ON s.username = u.username
                WHERE u.is_approved = 1
                ORDER BY s.nome
            """)
            return cursor.fetchall()
    
    def grade_submission(self, student_username, activity_title, grade, feedback):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE submissions
                SET grade = ?, feedback = ?
                WHERE student_username = ? AND activity_id = (
                    SELECT id FROM activities WHERE title = ?
                )
            """, (grade, feedback, student_username, activity_title))
            conn.commit()
            return True, "Nota atribuída com sucesso!"
    
    def run(self):
        """Inicia o loop principal da aplicação"""
        self.root.mainloop()

class RegisterScreen:
    def __init__(self, system, user_type):
        self.system = system
        self.user_type = user_type
        
        self.window = tk.Toplevel(system.root)
        self.window.title(f"Registro de {user_type.capitalize()}")
        
        if user_type == "aluno":
            self.window.geometry("600x700")
            self.setup_student_form()
        else:
            self.window.geometry("400x300")
            self.setup_basic_form()
    
    def setup_basic_form(self):
        tk.Label(self.window, text=f"Registro de {self.user_type.capitalize()}", 
                font=("Helvetica", 14)).pack(pady=20)
        
        form_frame = tk.Frame(self.window)
        form_frame.pack(padx=40, pady=10)
        
        tk.Label(form_frame, text="Usuário:").grid(row=0, column=0, sticky="w", pady=5)
        self.username_entry = tk.Entry(form_frame, font=("Helvetica", 12))
        self.username_entry.grid(row=0, column=1, sticky="ew", pady=5)
        
        tk.Label(form_frame, text="Senha:").grid(row=1, column=0, sticky="w", pady=5)
        self.password_entry = tk.Entry(form_frame, show="•", font=("Helvetica", 12))
        self.password_entry.grid(row=1, column=1, sticky="ew", pady=5)
        
        tk.Button(
            self.window,
            text="Registrar",
            command=self.register,
            bg="#2196F3",
            fg="white",
            font=("Helvetica", 12),
            pady=10
        ).pack(fill=tk.X, padx=40, pady=20)
    
    def setup_student_form(self):
        tk.Label(self.window, text="Cadastro de Aluno", 
                font=("Helvetica", 14, "bold")).pack(pady=20)
        
        form_frame = tk.Frame(self.window)
        form_frame.pack(padx=40, pady=10, fill=tk.BOTH, expand=True)
        
        # Configurar grid
        form_frame.columnconfigure(1, weight=1)
        
        # Campos do formulário com alinhamento correto
        fields = [
            ("Nome Completo:", "nome", 0),
            ("Matrícula:", "matricula", 1),
            ("Data Nascimento:", "data_nascimento", 2),
            ("CPF:", "cpf", 3),
            ("Curso:", "curso", 4),
            ("E-mail:", "email", 5),
            ("Telefone:", "telefone", 6),
            ("Endereço:", "endereco", 7)
        ]
        
        self.entries = {}
        
        for label, field, row in fields:
            tk.Label(form_frame, text=label, anchor="w").grid(
                row=row, column=0, sticky="ew", pady=5, padx=5)
            entry = tk.Entry(form_frame, font=("Helvetica", 12))
            entry.grid(row=row, column=1, sticky="ew", pady=5, padx=5)
            self.entries[field] = entry
        
        tk.Button(
            self.window,
            text="Cadastrar Aluno",
            command=self.register_student,
            bg="#4CAF50",
            fg="white",
            font=("Helvetica", 12),
            pady=10
        ).pack(fill=tk.X, padx=40, pady=20)
    
    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Erro", "Preencha todos os campos!")
            return
        
        success, message = self.system.register_user(username, password, self.user_type)
        messagebox.showinfo("Sucesso" if success else "Erro", message)
        if success:
            self.window.destroy()
    
    def register_student(self):
        student_data = {
            field: entry.get()
            for field, entry in self.entries.items()
        }
        
        # Validação dos campos obrigatórios
        required_fields = ['nome', 'matricula', 'cpf']
        for field in required_fields:
            if not student_data.get(field):
                messagebox.showerror("Erro", f"Campo obrigatório faltando: {field}")
                return
        
        success, message = self.system.register_student(student_data)
        messagebox.showinfo("Sucesso" if success else "Erro", message)
        if success:
            self.window.destroy()

class AdminPanel:
    def __init__(self, system):
        self.system = system
        
        self.window = tk.Toplevel()
        self.window.title("Painel de Administração")
        self.window.geometry("1000x600")
        
        self.setup_ui()
    
    def setup_ui(self):
        notebook = ttk.Notebook(self.window)
        notebook.pack(expand=True, fill=tk.BOTH)
        
        # Aba de aprovações
        approval_frame = ttk.Frame(notebook)
        notebook.add(approval_frame, text="Aprovar Cadastros")
        
        self.tree = ttk.Treeview(approval_frame, columns=("username", "type"), show="headings")
        self.tree.heading("username", text="Usuário")
        self.tree.heading("type", text="Tipo")
        self.tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        btn_frame = tk.Frame(approval_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(
            btn_frame,
            text="Aprovar",
            command=self.approve_user,
            bg="#4CAF50",
            fg="white"
        ).pack(side=tk.LEFT, expand=True, padx=5)
        
        tk.Button(
            btn_frame,
            text="Recusar",
            command=self.reject_user,
            bg="#F44336",
            fg="white"
        ).pack(side=tk.LEFT, expand=True, padx=5)
        
        tk.Button(
            btn_frame,
            text="Atualizar",
            command=self.load_requests,
            bg="#2196F3",
            fg="white"
        ).pack(side=tk.LEFT, expand=True, padx=5)
        
        self.load_requests()
    
    def load_requests(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        with sqlite3.connect(self.system.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT username, user_type FROM users WHERE is_approved=0
            """)
            
            for user in cursor.fetchall():
                self.tree.insert("", tk.END, values=(user["username"], user["user_type"]))
    
    def approve_user(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione um usuário!")
            return
        
        username = self.tree.item(selected)["values"][0]
        
        success, message = self.system.approve_student(username, "admin")
        messagebox.showinfo("Sucesso" if success else "Erro", message)
        self.load_requests()
    
    def reject_user(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione um usuário!")
            return
        
        username = self.tree.item(selected)["values"][0]
        
        with sqlite3.connect(self.system.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE username=?", (username,))
            
            if username.startswith("aluno_"):
                cursor.execute("DELETE FROM students WHERE username=?", (username,))
            
            conn.commit()
        
        messagebox.showinfo("Sucesso", f"Usuário {username} removido!")
        self.load_requests()

class ProfessorMainPanel:
    def __init__(self, system, professor_username):
        self.system = system
        self.professor_username = professor_username
        
        self.window = tk.Toplevel()
        self.window.title(f"Painel do Professor - {professor_username}")
        self.window.geometry("600x400")
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = tk.Frame(self.window)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=50)
        
        tk.Label(main_frame, text="Opções do Professor", 
                font=("Helvetica", 16, "bold")).pack(pady=20)
        
        # Botão para visualizar progresso geral
        tk.Button(
            main_frame,
            text="Visualizar Progresso Geral",
            command=self.show_class_progress,
            bg="#2196F3",
            fg="white",
            font=("Helvetica", 12),
            pady=15
        ).pack(fill=tk.X, pady=10)
        
        # Botão para visualizar progresso individual
        tk.Button(
            main_frame,
            text="Visualizar Progresso Individual",
            command=self.show_student_progress,
            bg="#4CAF50",
            fg="white",
            font=("Helvetica", 12),
            pady=15
        ).pack(fill=tk.X, pady=10)
        
        # Botão para atribuir nova atividade
        tk.Button(
            main_frame,
            text="Atribuir Nova Atividade",
            command=self.create_activity,
            bg="#FF9800",
            fg="white",
            font=("Helvetica", 12),
            pady=15
        ).pack(fill=tk.X, pady=10)
    
    def show_class_progress(self):
        ClassProgressPanel(self.system, self.professor_username)
    
    def show_student_progress(self):
        StudentSelectionPanel(self.system, self.professor_username)
    
    def create_activity(self):
        CreateActivityPanel(self.system, self.professor_username)

class ClassProgressPanel:
    def __init__(self, system, professor_username):
        self.system = system
        self.professor_username = professor_username
        
        self.window = tk.Toplevel()
        self.window.title("Progresso da Turma")
        self.window.geometry("1000x600")
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = tk.Frame(self.window)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Treeview para mostrar o progresso
        self.tree = ttk.Treeview(main_frame, columns=("nome", "matricula", "progresso", "entregas", "total"), 
                               show="headings")
        self.tree.heading("nome", text="Nome")
        self.tree.heading("matricula", text="Matrícula")
        self.tree.heading("progresso", text="Progresso (%)")
        self.tree.heading("entregas", text="Atividades Entregues")
        self.tree.heading("total", text="Total de Atividades")
        
        self.tree.column("nome", width=200)
        self.tree.column("matricula", width=100, anchor="center")
        self.tree.column("progresso", width=100, anchor="center")
        self.tree.column("entregas", width=150, anchor="center")
        self.tree.column("total", width=150, anchor="center")
        
        self.tree.pack(expand=True, fill=tk.BOTH)
        
        # Botão para atualizar
        tk.Button(
            main_frame,
            text="Atualizar",
            command=self.load_progress,
            bg="#2196F3",
            fg="white"
        ).pack(pady=10)
        
        self.load_progress()
    
    def load_progress(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        progress_data = self.system.get_class_progress()
        
        for student in progress_data:
            self.tree.insert("", tk.END, values=(
                student["nome"],
                student["matricula"],
                f"{student['progresso']:.1f}",
                student["entregas"],
                student["total_atividades"]
            ))

class StudentSelectionPanel:
    def __init__(self, system, professor_username):
        self.system = system
        self.professor_username = professor_username
        
        self.window = tk.Toplevel()
        self.window.title("Selecionar Aluno")
        self.window.geometry("600x400")
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = tk.Frame(self.window)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        tk.Label(main_frame, text="Selecione um aluno:", 
                font=("Helvetica", 12)).pack(pady=10)
        
        # Lista de alunos
        self.student_listbox = tk.Listbox(main_frame, font=("Helvetica", 12))
        self.student_listbox.pack(expand=True, fill=tk.BOTH, pady=10)
        
        # Botão para visualizar progresso
        tk.Button(
            main_frame,
            text="Visualizar Progresso",
            command=self.show_student_progress,
            bg="#4CAF50",
            fg="white",
            font=("Helvetica", 12),
            pady=10
        ).pack(fill=tk.X, pady=10)
        
        self.load_students()
    
    def load_students(self):
        self.student_listbox.delete(0, tk.END)
        students = self.system.get_all_students()
        
        for student in students:
            self.student_listbox.insert(tk.END, f"{student['nome']} - {student['matricula']}")
            self.student_listbox.data = students  # Armazenar dados completos
    
    def show_student_progress(self):
        selection = self.student_listbox.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um aluno!")
            return
        
        selected_student = self.student_listbox.data[selection[0]]
        StudentProgressPanel(self.system, self.professor_username, selected_student["username"])

class StudentProgressPanel:
    def __init__(self, system, professor_username, student_username):
        self.system = system
        self.professor_username = professor_username
        self.student_username = student_username
        
        self.window = tk.Toplevel()
        self.window.title("Progresso do Aluno")
        self.window.geometry("800x600")
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = tk.Frame(self.window)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Obter informações do aluno
        with sqlite3.connect(self.system.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT nome, matricula, progresso FROM students 
                WHERE username = ?
            """, (self.student_username,))
            student_info = cursor.fetchone()
        
        # Cabeçalho com informações do aluno
        header_frame = tk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(header_frame, 
                text=f"Aluno: {student_info['nome']} - Matrícula: {student_info['matricula']}",
                font=("Helvetica", 12, "bold")).pack(side=tk.LEFT)
        
        tk.Label(header_frame, 
                text=f"Progresso: {student_info['progresso']:.1f}%",
                font=("Helvetica", 12)).pack(side=tk.RIGHT)
        
        # Treeview para mostrar as atividades
        self.tree = ttk.Treeview(main_frame, columns=("atividade", "prazo", "entrega", "nota"), 
                                show="headings")
        self.tree.heading("atividade", text="Atividade")
        self.tree.heading("prazo", text="Prazo")
        self.tree.heading("entrega", text="Data de Entrega")
        self.tree.heading("nota", text="Nota")
        
        self.tree.column("atividade", width=300)
        self.tree.column("prazo", width=150)
        self.tree.column("entrega", width=150)
        self.tree.column("nota", width=100)
        
        self.tree.pack(expand=True, fill=tk.BOTH, pady=10)
        
        # Frame para atribuição de nota
        grade_frame = tk.Frame(main_frame)
        grade_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(grade_frame, text="Nota:").pack(side=tk.LEFT)
        self.grade_entry = tk.Entry(grade_frame, width=5)
        self.grade_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(grade_frame, text="Feedback:").pack(side=tk.LEFT, padx=(10,0))
        self.feedback_entry = tk.Entry(grade_frame, width=40)
        self.feedback_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        tk.Button(
            grade_frame,
            text="Atribuir Nota",
            command=self.assign_grade,
            bg="#FF9800",
            fg="white"
        ).pack(side=tk.RIGHT)
        
        # Botão para visualizar arquivo
        tk.Button(
            main_frame,
            text="Visualizar Arquivo Entregue",
            command=self.view_submission_file,
            bg="#2196F3",
            fg="white"
        ).pack(fill=tk.X, pady=5)
        
        self.load_submissions()
    
    def load_submissions(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        submissions = self.system.get_student_submissions(self.student_username)
        
        for sub in submissions:
            nota = sub["grade"] if sub["grade"] is not None else "Não avaliada"
            self.tree.insert("", tk.END, values=(
                sub["title"],
                sub["deadline"],
                sub["submission_date"],
                nota
            ), tags=(sub["file_path"],))
    
    def view_submission_file(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma atividade!")
            return
        
        file_path = self.tree.item(selected, "tags")[0]
        
        try:
            os.startfile(file_path)
        except:
            messagebox.showerror("Erro", "Não foi possível abrir o arquivo!")
    
    def assign_grade(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma atividade!")
            return
        
        activity_title = self.tree.item(selected)["values"][0]
        grade = self.grade_entry.get()
        feedback = self.feedback_entry.get()
        
        if not grade:
            messagebox.showwarning("Aviso", "Informe a nota!")
            return
        
        try:
            grade = float(grade)
            if grade < 0 or grade > 10:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Nota inválida! Deve ser um número entre 0 e 10.")
            return
        
        success, message = self.system.grade_submission(
            self.student_username, activity_title, grade, feedback
        )
        messagebox.showinfo("Sucesso" if success else "Erro", message)
        self.load_submissions()

class CreateActivityPanel:
    def __init__(self, system, professor_username):
        self.system = system
        self.professor_username = professor_username
        
        self.window = tk.Toplevel()
        self.window.title("Nova Atividade")
        self.window.geometry("500x400")
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = tk.Frame(self.window)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        tk.Label(main_frame, text="Criar Nova Atividade", 
                font=("Helvetica", 14, "bold")).pack(pady=10)
        
        # Campos do formulário
        tk.Label(main_frame, text="Título:", anchor="w").pack(fill=tk.X, pady=(10,0))
        self.title_entry = tk.Entry(main_frame, font=("Helvetica", 12))
        self.title_entry.pack(fill=tk.X, pady=5)
        
        tk.Label(main_frame, text="Descrição (opcional):", anchor="w").pack(fill=tk.X, pady=(10,0))
        self.desc_entry = tk.Text(main_frame, height=5, font=("Helvetica", 12))
        self.desc_entry.pack(fill=tk.X, pady=5)
        
        tk.Label(main_frame, text="Data Limite (DD/MM/AAAA):", anchor="w").pack(fill=tk.X, pady=(10,0))
        self.deadline_entry = tk.Entry(main_frame, font=("Helvetica", 12))
        self.deadline_entry.pack(fill=tk.X, pady=5)
        
        # Botão para criar atividade
        tk.Button(
            main_frame,
            text="Criar Atividade",
            command=self.create_activity,
            bg="#4CAF50",
            fg="white",
            font=("Helvetica", 12),
            pady=10
        ).pack(fill=tk.X, pady=20)
    
    def create_activity(self):
        title = self.title_entry.get()
        description = self.desc_entry.get("1.0", tk.END).strip()
        deadline = self.deadline_entry.get()
        
        if not title or not deadline:
            messagebox.showwarning("Aviso", "Preencha pelo menos o título e a data limite!")
            return
        
        try:
            # Validar data
            deadline_dt = datetime.strptime(deadline, "%d/%m/%Y")
            deadline_str = deadline_dt.strftime("%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Erro", "Formato de data inválido! Use DD/MM/AAAA.")
            return
        
        success, message = self.system.create_activity(title, description, deadline_str, self.professor_username)
        messagebox.showinfo("Sucesso" if success else "Erro", message)
        if success:
            self.window.destroy()

class StudentPanel:
    def __init__(self, system, student_username):
        self.system = system
        self.student_username = student_username
        
        self.window = tk.Toplevel()
        self.window.title(f"Painel do Aluno - {student_username}")
        self.window.geometry("800x600")
        
        self.setup_ui()
    
    def setup_ui(self):
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(expand=True, fill=tk.BOTH)
        
        # Aba de atividades
        self.setup_activities_tab()
        
        # Aba de notas
        self.setup_grades_tab()
        
        # Carregar dados iniciais
        self.load_activities()
        self.load_grades()
    
    def setup_activities_tab(self):
        activities_frame = ttk.Frame(self.notebook)
        self.notebook.add(activities_frame, text="Atividades")
        
        # Treeview para atividades
        self.activities_tree = ttk.Treeview(activities_frame, 
                                          columns=("title", "deadline", "status"), 
                                          show="headings")
        self.activities_tree.heading("title", text="Atividade")
        self.activities_tree.heading("deadline", text="Prazo")
        self.activities_tree.heading("status", text="Status")
        
        self.activities_tree.column("title", width=400)
        self.activities_tree.column("deadline", width=150)
        self.activities_tree.column("status", width=150)
        
        self.activities_tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Frame para entrega
        submission_frame = tk.Frame(activities_frame)
        submission_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.file_path_label = tk.Label(submission_frame, text="Nenhum arquivo selecionado")
        self.file_path_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Button(
            submission_frame,
            text="Selecionar Arquivo",
            command=self.select_file,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            submission_frame,
            text="Entregar",
            command=self.submit_activity,
            bg="#4CAF50",
            fg="white",
            width=15
        ).pack(side=tk.RIGHT)
    
    def setup_grades_tab(self):
        grades_frame = ttk.Frame(self.notebook)
        self.notebook.add(grades_frame, text="Notas")
        
        # Treeview para notas
        self.grades_tree = ttk.Treeview(grades_frame, 
                                      columns=("title", "grade", "feedback"), 
                                      show="headings")
        self.grades_tree.heading("title", text="Atividade")
        self.grades_tree.heading("grade", text="Nota")
        self.grades_tree.heading("feedback", text="Feedback")
        
        self.grades_tree.column("title", width=300)
        self.grades_tree.column("grade", width=100)
        self.grades_tree.column("feedback", width=300)
        
        self.grades_tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
    
    def load_activities(self):
        for item in self.activities_tree.get_children():
            self.activities_tree.delete(item)
        
        activities = self.system.get_activities_for_student(self.student_username)
        
        for act in activities:
            status = "Entregue" if act["submitted"] else "Pendente"
            self.activities_tree.insert("", tk.END, values=(
                act["title"],
                act["deadline"],
                status
            ), tags=(act["id"],))
    
    def load_grades(self):
        for item in self.grades_tree.get_children():
            self.grades_tree.delete(item)
        
        activities = self.system.get_activities_for_student(self.student_username)
        
        for act in activities:
            if act["submitted"] and act["grade"] is not None:
                self.grades_tree.insert("", tk.END, values=(
                    act["title"],
                    f"{act['grade']:.1f}",
                    act["feedback"] or ""
                ))
    
    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Selecione o arquivo para enviar",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        
        if file_path:
            self.file_path_label.config(text=file_path)
            self.selected_file = file_path
    
    def submit_activity(self):
        selected = self.activities_tree.focus()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma atividade!")
            return
        
        if not hasattr(self, 'selected_file'):
            messagebox.showwarning("Aviso", "Selecione um arquivo para enviar!")
            return
        
        activity_id = self.activities_tree.item(selected, "tags")[0]
        
        success, message = self.system.submit_activity(
            activity_id, self.student_username, self.selected_file
        )
        
        messagebox.showinfo("Sucesso" if success else "Erro", message)
        
        if success:
            self.load_activities()
            self.load_grades()
            self.file_path_label.config(text="Nenhum arquivo selecionado")
            delattr(self, 'selected_file')

# Executar o sistema
if __name__ == "__main__":
    app = AcademicSystem()
    app.run()