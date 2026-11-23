import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import dbC as db

ADMIN_PASSWORD = "123456"


class BlogApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestión de Blog - Neo4j Graph DB")
        self.geometry("1040x680")
        self.minsize(900, 580)

        self.usuario_activo_id = None
        self.usuario_activo_nombre = None
        self.dict_usuarios = {}
        self.articulos_db = {}
        self.admin_autenticado = False

        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.crear_interfaz()
        self.cargar_usuarios()
        self.cargar_articulos()

    def crear_interfaz(self):
        # Contenedor principal de pestañas
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Pestaña 1: Operación diaria del Blog
        self.tab_blog = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_blog, text=" 📰 Blog Público (Operación) ")

        # Pestaña 2: Administración y Restauración (Protegida por contraseña)
        self.tab_admin = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_admin, text=" 🔐 Administración y Auditoría ")

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        self._construir_tab_blog()
        self._construir_tab_admin()

    # PESTAÑA 1: BLOG PÚBLICO

    def _construir_tab_blog(self):
        top_bar = ttk.Frame(self.tab_blog, padding=10)
        top_bar.pack(fill=tk.X, side=tk.TOP)

        ttk.Label(top_bar, text="Usuario Activo:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=5)

        self.combo_usuarios = ttk.Combobox(top_bar, state="readonly", width=25)
        self.combo_usuarios.pack(side=tk.LEFT, padx=5)
        self.combo_usuarios.bind("<<ComboboxSelected>>", self.seleccionar_usuario)

        btn_nuevo_usuario = ttk.Button(top_bar, text="+ Registrar Usuario", command=self.modal_registrar_usuario)
        btn_nuevo_usuario.pack(side=tk.LEFT, padx=5)

        btn_ocultar_usuario = ttk.Button(top_bar, text="🗑 Eliminar Usuario", command=self.eliminar_usuario)
        btn_ocultar_usuario.pack(side=tk.LEFT, padx=5)

        btn_nuevo_articulo = ttk.Button(top_bar, text="✍ Publicar Artículo", command=self.modal_crear_articulo)
        btn_nuevo_articulo.pack(side=tk.RIGHT, padx=5)

        ttk.Separator(self.tab_blog, orient="horizontal").pack(fill=tk.X, padx=10, pady=5)

        main_paned = ttk.PanedWindow(self.tab_blog, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Panel Izquierdo: Lista de artículos activos
        left_frame = ttk.Labelframe(main_paned, text=" Artículos Publicados ", padding=10)
        main_paned.add(left_frame, weight=1)

        columns = ("id", "titulo", "autor", "comentarios")
        self.tree_articulos = ttk.Treeview(left_frame, columns=columns, show="headings", selectmode="browse")
        self.tree_articulos.heading("id", text="ID")
        self.tree_articulos.heading("titulo", text="Título")
        self.tree_articulos.heading("autor", text="Autor")
        self.tree_articulos.heading("comentarios", text="Comentarios")

        self.tree_articulos.column("id", width=40, anchor="center")
        self.tree_articulos.column("titulo", width=180)
        self.tree_articulos.column("autor", width=95)
        self.tree_articulos.column("comentarios", width=85, anchor="center")

        self.tree_articulos.pack(fill=tk.BOTH, expand=True)
        self.tree_articulos.bind("<<TreeviewSelect>>", self.on_articulo_seleccionado)

        # Panel Derecho: Lectura, taxonomías y comentarios
        right_frame = ttk.Labelframe(main_paned, text=" Lectura del Artículo y Comentarios ", padding=10)
        main_paned.add(right_frame, weight=2)

        self.lbl_titulo = ttk.Label(right_frame, text="Seleccione un artículo para leer", font=("Helvetica", 14, "bold"))
        self.lbl_titulo.pack(anchor=tk.W, pady=5)

        self.lbl_meta = ttk.Label(right_frame, text="", font=("Helvetica", 9, "italic"))
        self.lbl_meta.pack(anchor=tk.W, pady=2)

        self.lbl_tags = ttk.Label(right_frame, text="", font=("Helvetica", 9))
        self.lbl_tags.pack(anchor=tk.W, pady=2)

        self.txt_contenido = tk.Text(right_frame, wrap=tk.WORD, height=10)
        self.txt_contenido.pack(fill=tk.BOTH, expand=True, pady=5)

        btn_box = ttk.Frame(right_frame)
        btn_box.pack(fill=tk.X, pady=5)

        ttk.Button(btn_box, text="💬 Agregar Comentario", command=self.modal_agregar_comentario).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_box, text="🗑 Eliminar Comentario", command=self.eliminar_comentario).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_box, text="🏷 Agregar Tag", command=lambda: self.modal_asignar_taxonomia("tag")).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_box, text="📂 Agregar Categoría", command=lambda: self.modal_asignar_taxonomia("categoria")).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_box, text="🗑 Eliminar Artículo", command=self.eliminar_articulo).pack(side=tk.RIGHT, padx=2)

        ttk.Label(right_frame, text="Comentarios:", font=("Helvetica", 10, "bold")).pack(anchor=tk.W, pady=(10, 2))

        self.txt_comentarios = tk.Text(right_frame, wrap=tk.WORD, height=5, state=tk.DISABLED)
        self.txt_comentarios.pack(fill=tk.X, pady=5)

    # PESTAÑA 2: PANEL DE ADMINISTRACIÓN Y AUDITORÍA (Protegido con clave)

    def _construir_tab_admin(self):
        header = ttk.Frame(self.tab_admin, padding=10)
        header.pack(fill=tk.X)

        ttk.Label(
            header,
            text="Panel de Administración, Restauración y Auditoría del Grafo",
            font=("Helvetica", 12, "bold")
        ).pack(side=tk.LEFT)

        ttk.Button(header, text="🔒 Bloquear Panel", command=self.bloquear_admin).pack(side=tk.RIGHT, padx=5)
        ttk.Button(header, text="🔄 Actualizar Listados", command=self.refrescar_panel_admin).pack(side=tk.RIGHT, padx=5)

        # Sub-pestañas internas para organizar Restauraciones y Auditoría
        sub_notebook = ttk.Notebook(self.tab_admin)
        sub_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Sub-tab A: Restaurar Usuarios
        frame_u = ttk.Frame(sub_notebook, padding=10)
        sub_notebook.add(frame_u, text="Usuarios Inactivos")

        ttk.Label(
            frame_u,
            text="Nota: Al reactivar un usuario, sus publicaciones y comentarios ocultos deben restaurarse individualmente.",
            font=("Helvetica", 9, "italic")
        ).pack(anchor=tk.W, pady=(0, 6))

        self.tree_inact_users = ttk.Treeview(frame_u, columns=("id", "nombre", "email"), show="headings", selectmode="browse")
        self.tree_inact_users.heading("id", text="ID")
        self.tree_inact_users.heading("nombre", text="Nombre")
        self.tree_inact_users.heading("email", text="Email")
        self.tree_inact_users.column("id", width=60, anchor="center")
        self.tree_inact_users.column("nombre", width=220)
        self.tree_inact_users.column("email", width=260)
        self.tree_inact_users.pack(fill=tk.BOTH, expand=True)

        ttk.Button(frame_u, text="♻ Restaurar Usuario Seleccionado", command=self.restaurar_usuario).pack(pady=8)

        # Sub-tab B: Restaurar Artículos
        frame_a = ttk.Frame(sub_notebook, padding=10)
        sub_notebook.add(frame_a, text="Artículos Inactivos")

        self.tree_inact_arts = ttk.Treeview(frame_a, columns=("id", "titulo", "autor"), show="headings", selectmode="browse")
        self.tree_inact_arts.heading("id", text="ID")
        self.tree_inact_arts.heading("titulo", text="Título")
        self.tree_inact_arts.heading("autor", text="Autor")
        self.tree_inact_arts.column("id", width=60, anchor="center")
        self.tree_inact_arts.column("titulo", width=350)
        self.tree_inact_arts.column("autor", width=180)
        self.tree_inact_arts.pack(fill=tk.BOTH, expand=True)

        ttk.Button(frame_a, text="♻ Restaurar Artículo Seleccionado", command=self.restaurar_articulo).pack(pady=8)

        # Sub-tab C: Restaurar Comentarios
        frame_c = ttk.Frame(sub_notebook, padding=10)
        sub_notebook.add(frame_c, text="Comentarios Inactivos")

        self.tree_inact_comms = ttk.Treeview(
            frame_c, columns=("id", "art_id", "autor", "texto"), show="headings", selectmode="browse"
        )
        self.tree_inact_comms.heading("id", text="ID Comentario")
        self.tree_inact_comms.heading("art_id", text="ID Artículo")
        self.tree_inact_comms.heading("autor", text="Autor")
        self.tree_inact_comms.heading("texto", text="Contenido")
        self.tree_inact_comms.column("id", width=100, anchor="center")
        self.tree_inact_comms.column("art_id", width=90, anchor="center")
        self.tree_inact_comms.column("autor", width=150)
        self.tree_inact_comms.column("texto", width=400)
        self.tree_inact_comms.pack(fill=tk.BOTH, expand=True)

        ttk.Button(frame_c, text="♻ Restaurar Comentario Seleccionado", command=self.restaurar_comentario).pack(pady=8)

        # Sub-tab D: Auditoría General
        frame_aud = ttk.Frame(sub_notebook, padding=10)
        sub_notebook.add(frame_aud, text="Auditoría General (Todos los Artículos)")

        cols_aud = ("id", "titulo", "autor", "estado", "fecha", "tags", "categorias")
        self.tree_auditoria = ttk.Treeview(frame_aud, columns=cols_aud, show="headings", selectmode="browse")
        self.tree_auditoria.heading("id", text="ID")
        self.tree_auditoria.heading("titulo", text="Título")
        self.tree_auditoria.heading("autor", text="Autor")
        self.tree_auditoria.heading("estado", text="Estado")
        self.tree_auditoria.heading("fecha", text="Fecha")
        self.tree_auditoria.heading("tags", text="Tags")
        self.tree_auditoria.heading("categorias", text="Categorías")

        self.tree_auditoria.column("id", width=45, anchor="center")
        self.tree_auditoria.column("titulo", width=200)
        self.tree_auditoria.column("autor", width=110)
        self.tree_auditoria.column("estado", width=85, anchor="center")
        self.tree_auditoria.column("fecha", width=120, anchor="center")
        self.tree_auditoria.column("tags", width=160)
        self.tree_auditoria.column("categorias", width=160)
        self.tree_auditoria.pack(fill=tk.BOTH, expand=True)

    # CONTROL DE ACCESO AL PANEL DE ADMINISTRACIÓN

    def on_tab_changed(self, event):
        pestana_actual = self.notebook.index(self.notebook.select())
        if pestana_actual == 1:  # Pestaña de Administración
            if not self.admin_autenticado:
                clave = simpledialog.askstring(
                    "Acceso Restringido",
                    "Ingrese la contraseña de administrador:",
                    show="*",
                    parent=self
                )
                if clave == ADMIN_PASSWORD:
                    self.admin_autenticado = True
                    self.refrescar_panel_admin()
                else:
                    if clave is not None:
                        messagebox.showerror("Acceso Denegado", "Contraseña incorrecta.", parent=self)
                    self.notebook.select(0)
            else:
                self.refrescar_panel_admin()

    def bloquear_admin(self):
        self.admin_autenticado = False
        self.notebook.select(0)
        messagebox.showinfo("Sesión Cerrada", "Panel de administración bloqueado.", parent=self)

    def refrescar_panel_admin(self):
        try:
            # 1. Usuarios inactivos
            for item in self.tree_inact_users.get_children():
                self.tree_inact_users.delete(item)
            for u in db.obtener_usuarios_inactivos():
                self.tree_inact_users.insert("", tk.END, iid=str(u[0]), values=u)

            # 2. Artículos inactivos
            for item in self.tree_inact_arts.get_children():
                self.tree_inact_arts.delete(item)
            for a in db.obtener_articulos_inactivos():
                self.tree_inact_arts.insert("", tk.END, iid=str(a[0]), values=a)

            # 3. Comentarios inactivos
            for item in self.tree_inact_comms.get_children():
                self.tree_inact_comms.delete(item)
            for c in db.obtener_comentarios_inactivos():
                self.tree_inact_comms.insert("", tk.END, iid=str(c[0]), values=c)

            # 4. Auditoría general
            for item in self.tree_auditoria.get_children():
                self.tree_auditoria.delete(item)
            for row in db.auditoria_general_articulos():
                self.tree_auditoria.insert("", tk.END, iid=str(row[0]), values=row)
        except Exception as e:
            messagebox.showerror("Error de Auditoría", f"No se pudieron cargar los datos:\n{e}", parent=self)

    def restaurar_usuario(self):
        sel = self.tree_inact_users.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un usuario inactivo de la lista.", parent=self)
            return
        user_id = int(sel[0])
        try:
            db.restaurar_usuario_logico(user_id)
            messagebox.showinfo("Éxito", f"Usuario ID {user_id} restaurado a estado ACTIVO.", parent=self)
            self.refrescar_panel_admin()
            self.cargar_usuarios()
            self.cargar_articulos()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo restaurar el usuario:\n{e}", parent=self)

    def restaurar_articulo(self):
        sel = self.tree_inact_arts.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un artículo inactivo de la lista.", parent=self)
            return
        art_id = int(sel[0])
        try:
            db.restaurar_articulo_logico(art_id)
            messagebox.showinfo("Éxito", f"Artículo ID {art_id} restaurado a estado ACTIVO.", parent=self)
            self.refrescar_panel_admin()
            self.cargar_articulos()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo restaurar el artículo:\n{e}", parent=self)

    def restaurar_comentario(self):
        sel = self.tree_inact_comms.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione un comentario inactivo de la lista.", parent=self)
            return
        comm_id = int(sel[0])
        try:
            db.restaurar_comentario_logico(comm_id)
            messagebox.showinfo("Éxito", f"Comentario ID {comm_id} restaurado a estado ACTIVO.", parent=self)
            self.refrescar_panel_admin()
            self.cargar_articulos()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo restaurar el comentario:\n{e}", parent=self)

    # LÓGICA DE OPERACIÓN (Usuarios, Artículos, Comentarios, Taxonomías)

    def cargar_usuarios(self):
        try:
            usuarios = db.obtener_usuarios()
            self.dict_usuarios = {f"{u[1]} ({u[2]})": u[0] for u in usuarios}
            self.combo_usuarios["values"] = list(self.dict_usuarios.keys())

            if usuarios:
                self.combo_usuarios.current(0)
                self.seleccionar_usuario(None)
            else:
                self.combo_usuarios.set("")
                self.usuario_activo_id = None
                self.usuario_activo_nombre = None
        except Exception as e:
            messagebox.showerror("Error de Base de Datos", f"No se pudieron cargar usuarios:\n{e}")

    def seleccionar_usuario(self, event):
        seleccion = self.combo_usuarios.get()
        if seleccion in self.dict_usuarios:
            self.usuario_activo_id = self.dict_usuarios[seleccion]
            self.usuario_activo_nombre = seleccion.split(" (")[0]

    def cargar_articulos(self):
        for item in self.tree_articulos.get_children():
            self.tree_articulos.delete(item)

        self.articulos_db.clear()

        try:
            articulos = db.listar_articulos()
            for art in articulos:
                art_id = str(art[0])
                self.articulos_db[art_id] = art
                self.tree_articulos.insert("", tk.END, iid=art_id, values=(art[0], art[1], art[2], art[5]))
        except Exception as e:
            messagebox.showerror("Error", f"Error al listar artículos:\n{e}")

    def on_articulo_seleccionado(self, event):
        selected_item = self.tree_articulos.selection()
        if not selected_item:
            return

        art_id = str(selected_item[0])
        art = self.articulos_db.get(art_id)
        if not art:
            return

        _, titulo, autor, fecha, texto, _ = art

        self.lbl_titulo.config(text=titulo)
        self.lbl_meta.config(text=f"Por: {autor} | Fecha: {fecha}")

        self.txt_contenido.delete("1.0", tk.END)
        self.txt_contenido.insert(tk.END, texto)

        self.cargar_comentarios(int(art_id))
        self.refrescar_taxonomia(int(art_id))

    def cargar_comentarios(self, article_id):
        self.txt_comentarios.config(state=tk.NORMAL)
        self.txt_comentarios.delete("1.0", tk.END)

        try:
            comentarios = db.obtener_comentarios(article_id)
            if not comentarios:
                self.txt_comentarios.insert(tk.END, "Aún no hay comentarios activos en este artículo.")
            else:
                for c in comentarios:
                    self.txt_comentarios.insert(tk.END, f"• [ID: {c[0]}] {c[1]}: {c[2]}\n")
        except Exception as e:
            self.txt_comentarios.insert(tk.END, f"Error al cargar comentarios: {e}")

        self.txt_comentarios.config(state=tk.DISABLED)

    def refrescar_taxonomia(self, article_id):
        try:
            partes = []
            tags = db.obtener_tags(article_id)
            categorias = db.obtener_categorias(article_id)
            if tags:
                partes.append(f"🏷 Tags: {tags}")
            if categorias:
                partes.append(f"📂 Categorías: {categorias}")
            self.lbl_tags.config(text="  |  ".join(partes))
        except Exception as e:
            self.lbl_tags.config(text=f"Error al cargar tags/categorías: {e}")

    def modal_asignar_taxonomia(self, tipo):
        selected_item = self.tree_articulos.selection()
        if not selected_item:
            messagebox.showwarning("Atención", "Seleccione un artículo de la lista.")
            return

        art_id = int(selected_item[0])
        etiqueta = "Tag" if tipo == "tag" else "Categoría"
        nombre = simpledialog.askstring(f"Nueva {etiqueta}", f"Nombre de la {etiqueta.lower()}:", parent=self)
        if not nombre:
            return

        try:
            if tipo == "tag":
                db.agregar_tag(art_id, nombre.strip())
            else:
                db.agregar_categoria(art_id, nombre.strip())
            messagebox.showinfo("Éxito", f"{etiqueta} asignada correctamente.")
            self.refrescar_taxonomia(art_id)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo asignar la {etiqueta.lower()}:\n{e}")

    def modal_registrar_usuario(self):
        nombre = simpledialog.askstring("Nuevo Usuario", "Ingrese Nombre:", parent=self)
        if not nombre:
            return
        email = simpledialog.askstring("Nuevo Usuario", "Ingrese Email:", parent=self)
        if not email:
            return

        try:
            new_id = db.guardar_usuario(nombre.strip(), email.strip())
            messagebox.showinfo("Éxito", f"Usuario registrado exitosamente con ID: {new_id}")
            self.cargar_usuarios()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el usuario:\n{e}")

    def eliminar_usuario(self):
        if not self.usuario_activo_id:
            messagebox.showwarning("Atención", "No hay ningún usuario activo seleccionado.")
            return

        confirmar = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Desea eliminar al usuario '{self.usuario_activo_nombre}'?\n\n(Sus publicaciones dejarán de mostrarse mientras esté inactivo).",
            parent=self
        )

        if confirmar:
            try:
                db.eliminar_usuario_logico(self.usuario_activo_id)
                messagebox.showinfo("Éxito", "Usuario eliminado correctamente.")
                self.cargar_usuarios()
                self.cargar_articulos()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el usuario:\n{e}")

    def modal_crear_articulo(self):
        if not self.usuario_activo_id:
            messagebox.showwarning("Atención", "Seleccione o registre un usuario primero.")
            return

        win = tk.Toplevel(self)
        win.title("Publicar Nuevo Artículo")
        win.geometry("500x400")

        ttk.Label(win, text="Título:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        entry_titulo = ttk.Entry(win, width=60)
        entry_titulo.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(win, text="Contenido:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        txt_contenido = tk.Text(win, wrap=tk.WORD, height=12)
        txt_contenido.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        def guardar():
            tit = entry_titulo.get().strip()
            text = txt_contenido.get("1.0", tk.END).strip()
            if not tit or not text:
                messagebox.showwarning("Incompleto", "Ingrese título y contenido.", parent=win)
                return

            try:
                db.crear_articulo(self.usuario_activo_id, tit, text)
                messagebox.showinfo("Éxito", "Artículo publicado correctamente.", parent=win)
                win.destroy()
                self.cargar_articulos()
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar:\n{e}", parent=win)

        ttk.Button(win, text="Publicar", command=guardar).pack(pady=10)

    def eliminar_articulo(self):
        selected_item = self.tree_articulos.selection()
        if not selected_item:
            messagebox.showwarning("Atención", "Seleccione un artículo de la lista.")
            return

        art_id = int(selected_item[0])
        confirmar = messagebox.askyesno(
            "Confirmar Eliminación",
            "¿Desea eliminar esta publicación del sistema público?",
            parent=self
        )

        if confirmar:
            try:
                db.eliminar_articulo_logico(art_id)
                messagebox.showinfo("Éxito", "La publicación ha sido eliminada correctamente.")
                self.lbl_titulo.config(text="Seleccione un artículo para leer")
                self.lbl_meta.config(text="")
                self.lbl_tags.config(text="")
                self.txt_contenido.delete("1.0", tk.END)
                self.txt_comentarios.config(state=tk.NORMAL)
                self.txt_comentarios.delete("1.0", tk.END)
                self.txt_comentarios.config(state=tk.DISABLED)
                self.cargar_articulos()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo ocultar el artículo:\n{e}")

    def modal_agregar_comentario(self):
        selected_item = self.tree_articulos.selection()
        if not selected_item:
            messagebox.showwarning("Atención", "Seleccione un artículo para comentar.")
            return

        art_id = int(selected_item[0])
        texto_comentario = simpledialog.askstring("Nuevo Comentario", "Escriba su comentario:", parent=self)
        if not texto_comentario:
            return

        try:
            nombre = self.usuario_activo_nombre or "Anónimo"
            db.agregar_comentario(art_id, self.usuario_activo_id, nombre, None, texto_comentario.strip())
            messagebox.showinfo("Éxito", "Comentario agregado.")
            self.cargar_articulos()
            self.cargar_comentarios(art_id)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el comentario:\n{e}")

    def eliminar_comentario(self):
        selected_item = self.tree_articulos.selection()
        if not selected_item:
            messagebox.showwarning("Atención", "Seleccione un artículo primero para ver sus comentarios.")
            return

        comment_id = simpledialog.askinteger("Eliminar Comentario", "Ingrese el ID del comentario a eliminar:", parent=self)
        if not comment_id:
            return

        try:
            db.eliminar_comentario_logico(comment_id)
            messagebox.showinfo("Éxito", f"Comentario #{comment_id} eliminado.")
            art_id = int(selected_item[0])
            self.cargar_articulos()
            self.cargar_comentarios(art_id)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el comentario:\n{e}")


if __name__ == "__main__":
    app = BlogApp()
    app.mainloop()