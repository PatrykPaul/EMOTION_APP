# gui.py
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from PIL import Image, ImageTk

from chatbot_config import ConversationState, handle_user_message

# ===== UI =====
BG_APP      = "#f8f9fa"
IN_BG       = "#F5F7FB"; IN_BORDER = "#E2E8F0"
OUT_BG      = "#EAF2FF"; OUT_BORDER = "#4E8FFF"
SHADOW      = "#E7ECF5"; TEXT_BODY = "#111827"

MAX_BUBBLE_W = 480
SIDE_MARGIN  = 16
PAD_X, PAD_Y = 10, 8
RADIUS       = 10
BORDER_W     = 1

EMO_BTN_SIZE = (180, 48)  # rozmiar kafelka z obrazkiem (stały)


def round_rect(c, x1, y1, x2, y2, r=10, **kw):
    pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y2-r, x2,y2, x2-r,y2,
           x1+r,y2, x1,y2, x1,y2-r, x1,y1+r, x1,y1]
    return c.create_polygon(pts, smooth=True, **kw)


def measure_height(parent, text, width_px, font):
    tmp = tk.Canvas(parent)
    tid = tmp.create_text(0, 0, text=text, anchor="nw", width=width_px, font=font)
    tmp.update_idletasks()
    x1, y1, x2, y2 = tmp.bbox(tid)
    tmp.destroy()
    return max(y2 - y1, 14)


def create_app():
    """
    Tworzy główne okno launchera i cały GUI.
    Zwraca root, na którym main.py wywoła root.mainloop().
    """
    root = tb.Window(themename="flatly")
    root.title("Emotions Chat – Launcher")
    root.geometry("420x260")

    popup = None  # referencja do okna chatu (wewnątrz closure)

    def pokaz_popup():
        nonlocal popup
        if popup and popup.winfo_exists():
            popup.lift()
            return

        # stan rozmowy dla TEGO okna
        state = ConversationState()

        popup = tk.Toplevel(root)
        popup.title("Emotions Chat")
        popup.configure(bg=BG_APP)

        # większe okno, ale w granicach ekranu
        sw, sh = popup.winfo_screenwidth(), popup.winfo_screenheight()
        w, h = min(900, sw - 40), min(720, sh - 80)
        popup.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        popup.minsize(640, 520)
        popup.resizable(True, True)

        # === Nagłówek: obraz skalowany na pełną szerokość ===
        header_holder = tk.Label(popup, borderwidth=0, bg=BG_APP)
        header_holder.pack(fill=tk.X, side=tk.TOP)

        try:
            popup._header_src = Image.open("Images/top.png")  # zapamiętaj źródło
        except Exception:
            popup._header_src = None

        def update_header(_=None):
            if popup._header_src is None:
                header_holder.config(text="Emotions Chat", font=("Segoe UI", 14, "bold"))
                return
            target_w = popup.winfo_width()
            if target_w < 300:
                return
            target_h = 96
            img = popup._header_src.resize((target_w, target_h), Image.Resampling.LANCZOS)
            popup._header_img = ImageTk.PhotoImage(img)  # trzymaj referencję
            header_holder.configure(image=popup._header_img)

        popup.bind("<Configure>", update_header)  # skaluj przy zmianie rozmiaru
        popup.after(50, update_header)

        # === Obszar wiadomości (scrollowany) ===
        messages_container = tk.Frame(popup, bg=BG_APP)
        messages_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=16, pady=(8, 4))

        canvas = tk.Canvas(messages_container, bg=BG_APP, highlightthickness=0, bd=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll_y = tk.Scrollbar(messages_container, orient=tk.VERTICAL, command=canvas.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=scroll_y.set)

        messages = tk.Frame(canvas, bg=BG_APP)
        win_id = canvas.create_window((0, 0), window=messages, anchor="nw")

        messages.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win_id, width=e.width))

        # === Pole wpisu (na dole) ===
        input_bar = tb.Frame(popup, padding=(12, 8))
        input_bar.pack(side=tk.BOTTOM, fill=tk.X)
        entry = tk.Text(input_bar, height=3, wrap="word")
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        send_btn = tb.Button(input_bar, text="Wyślij", bootstyle=PRIMARY)
        send_btn.pack(side=tk.RIGHT)

        # === Funkcja dodająca bąbel ===
        def add_bubble(text, outgoing=False):
            body_font = ("Segoe UI", 10)
            track_w = max(360, canvas.winfo_width() or (w - 2*SIDE_MARGIN))
            text_w  = max(140, min(MAX_BUBBLE_W, track_w - 2*SIDE_MARGIN) - 2*PAD_X)
            h_body  = measure_height(messages, text, text_w, body_font)
            bub_h   = PAD_Y + h_body + PAD_Y
            bub_w   = text_w + 2*PAD_X

            row = tk.Frame(messages, bg=BG_APP)
            row.pack(fill="x", pady=(4, 2))
            c = tk.Canvas(row, height=bub_h + 6, bg=BG_APP, highlightthickness=0, bd=0)
            c.pack(fill="x")

            if outgoing:
                left = track_w - bub_w - SIDE_MARGIN
                fill, border = OUT_BG, OUT_BORDER
            else:
                left = SIDE_MARGIN
                fill, border = IN_BG, IN_BORDER

            round_rect(c, left+2, 4, left+bub_w+2, bub_h+4, r=RADIUS, fill=SHADOW, outline="", width=0)
            round_rect(c, left, 0, left+bub_w, bub_h, r=RADIUS, fill=fill, outline=border, width=BORDER_W)
            c.create_text(left+PAD_X, PAD_Y, text=text, anchor="nw",
                          font=body_font, fill=TEXT_BODY, width=text_w)

            popup.after(10, lambda: canvas.yview_moveto(1.0))

        # === Start: pierwsze pytanie z INITIAL_QUESTIONS ===
        first_q = state.get_current_question_text()
        if first_q:
            add_bubble(first_q, outgoing=False)
        else:
            add_bubble("Welcome to Emotions Chat! 🧊", outgoing=False)

        # === Pasek emocji – obrazki z przewijaniem; klik = WYŚLIJ ===
        emotions_bar = tb.Frame(popup, padding=(12, 6))
        emotions_bar.pack(side=tk.BOTTOM, fill=tk.X)

        btn_left  = tb.Button(emotions_bar, text="⟵", width=3, bootstyle=SECONDARY)
        btn_right = tb.Button(emotions_bar, text="⟶", width=3, bootstyle=SECONDARY)
        btn_left.pack(side=tk.LEFT, padx=(0, 6))
        btn_right.pack(side=tk.RIGHT, padx=(6, 0))

        emo_canvas = tk.Canvas(emotions_bar, height=EMO_BTN_SIZE[1] + 8,
                               bg=BG_APP, highlightthickness=0, bd=0)
        emo_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)

        emo_inner = tk.Frame(emo_canvas, bg=BG_APP)
        emo_canvas.create_window((0, 0), window=emo_inner, anchor="nw")
        emo_inner.bind("<Configure>", lambda e: emo_canvas.configure(scrollregion=emo_canvas.bbox("all")))

        EMO_FILES = [
            ("Zaskoczony",   "Images/zaskoczony.png"),
            ("Szczęśliwy",   "Images/szczęśliwy.png"),
            ("Lękliwy",      "Images/lękliwy.png"),
            ("Rozgniewany",  "Images/Rozgniewany.png"),
            ("Zniesmaczony", "Images/zniesmaczony.png"),
            ("Smutny",       "Images/smutny.png"),
        ]
        popup._emo_imgs = []

        def on_emotion_click(text_to_send):
            # użytkownikowa wiadomość
            add_bubble(text_to_send, outgoing=True)
            # odpowiedź bota
            reply = handle_user_message(text_to_send, state)
            if reply:
                add_bubble(reply, outgoing=False)

        for label, path in EMO_FILES:
            try:
                img = Image.open(path).resize(EMO_BTN_SIZE, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                popup._emo_imgs.append(photo)
                tk.Button(emo_inner, image=photo, borderwidth=0, relief="flat",
                          bg=BG_APP, activebackground=BG_APP,
                          command=lambda t=label: on_emotion_click(t)
                          ).pack(side=tk.LEFT, padx=6)
            except Exception:
                tb.Button(emo_inner, text=label, bootstyle=SECONDARY,
                          padding=(10, 6),
                          command=lambda t=label: on_emotion_click(t)
                          ).pack(side=tk.LEFT, padx=6)

        btn_left.configure(command=lambda: emo_canvas.xview_scroll(-4, "units"))
        btn_right.configure(command=lambda: emo_canvas.xview_scroll(4, "units"))

        # === wysyłanie z pola tekstowego ===
        def send_message(_=None):
            t = entry.get("1.0", "end").strip()
            if not t:
                return
            add_bubble(t, outgoing=True)
            entry.delete("1.0", "end")

            reply = handle_user_message(t, state)
            if reply:
                add_bubble(reply, outgoing=False)

        def on_key(event):
            if event.keysym == "Return" and not (event.state & 0x0001):
                send_message()
                return "break"

        entry.bind("<KeyPress>", on_key)
        send_btn.configure(command=send_message)

        # scroll kółkiem tylko nad historią
        def _on_mousewheel(event):
            if event.delta:
                delta = -1 * (event.delta // 120)
            else:
                delta = 1 if event.num == 5 else -1
            canvas.yview_scroll(delta, "units")

        def bind_wheel(_):   canvas.bind_all("<MouseWheel>", _on_mousewheel)
        def unbind_wheel(_): canvas.unbind_all("<MouseWheel>")
        canvas.bind("<Enter>", bind_wheel)
        canvas.bind("<Leave>", unbind_wheel)

    # ===== Launcher UI =====
    tb.Label(root, text="Kliknij, aby otworzyć chat:", font=("Segoe UI", 11)).pack(pady=(28, 8))
    tb.Button(root, text="Pokaż chat", bootstyle=PRIMARY, command=pokaz_popup).pack()
    tb.Label(root, text="(nagłówek skaluje się • emocje wysyłają od razu)",
             bootstyle=SECONDARY).pack(pady=10)

    return root
