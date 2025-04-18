
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.simpledialog import Dialog
from tkcalendar import DateEntry
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd

PRESET_CATEGORIES = [
    "На карту (Шаяна)",
    "Нал от Шаяны (USD)",
    "Нал от Шаяны (UZS)",
    "На карту (Кайзер)",
    "Премия / Подарок"
]

DATA_FILE = "data.json"

class FinanceTracker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Finance Tracker")
        self.geometry("1150x750")

        self.data = self.load_data()
        self.categories = self.load_categories()
        self.filtered_data = self.data.copy()
        self.sort_reverse = False
        self.rate_visible = True

        self.create_widgets()
        self.update_filter_options()
        self.update_table()

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return []
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("transactions", [])
        except:
            return []

    def load_categories(self):
        if not os.path.exists(DATA_FILE):
            return PRESET_CATEGORIES.copy()
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("categories", PRESET_CATEGORIES.copy())
        except:
            return PRESET_CATEGORIES.copy()

    def save_all(self):
        if not self.data:
            self.data = []
        if not self.categories:
            self.categories = PRESET_CATEGORIES.copy()
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"transactions": self.data, "categories": self.categories}, f, ensure_ascii=False, indent=4)
    def create_widgets(self):
        filter_frame = ttk.LabelFrame(self, text="Фильтры")
        filter_frame.pack(fill="x", padx=10, pady=5)

        self.year_var = tk.StringVar()
        self.month_var = tk.StringVar()
        self.category_var = tk.StringVar()

        self.year_combo = ttk.Combobox(filter_frame, textvariable=self.year_var, width=10)
        self.month_combo = ttk.Combobox(filter_frame, textvariable=self.month_var, width=10)
        self.category_combo = ttk.Combobox(filter_frame, textvariable=self.category_var, width=30)

        for label, widget in zip(["Год", "Месяц", "Категория"],
                                 [self.year_combo, self.month_combo, self.category_combo]):
            ttk.Label(filter_frame, text=label).pack(side="left", padx=5)
            widget.pack(side="left", padx=5)

        ttk.Button(filter_frame, text="Применить", command=self.apply_filters).pack(side="left", padx=10)
        ttk.Button(filter_frame, text="Сбросить", command=self.reset_filters).pack(side="left")

        # Таблица
        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ["Дата", "UZS", "USD", "Курс", "Итог в UZS", "Категория", "Комментарий"]
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, anchor="w", width=140)
        self.tree.column("Комментарий", width=260)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.bind("<Double-1>", self.show_details)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Итог
        self.total_label = ttk.Label(self, text="", font=("Arial", 12, "bold"))
        self.total_label.pack(pady=(0, 10))

        # Кнопки
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="➕ Добавить", command=self.add_record).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="✏️ Редактировать", command=self.edit_record).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Удалить", command=self.delete_record).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="📊 График", command=self.plot_data).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="📤 Экспорт", command=self.export_to_excel).pack(side="left", padx=5)
        self.toggle_rate_btn = ttk.Button(btn_frame, text="Скрыть курс", command=self.toggle_rate_column)
        self.toggle_rate_btn.pack(side="left", padx=5)

    def toggle_rate_column(self):
        show = not self.rate_visible
        self.tree.column("Курс", width=100 if show else 0, minwidth=0, stretch=show)
        self.rate_visible = show
        self.toggle_rate_btn.config(text="Показать курс" if not show else "Скрыть курс")

    def update_filter_options(self):
        years = sorted(set(d["date"][:4] for d in self.data), reverse=True)
        months = sorted(set(d["date"][5:7] for d in self.data))
        self.year_combo["values"] = [""] + years
        self.month_combo["values"] = [""] + months
        self.category_combo["values"] = [""] + sorted(set(self.categories))

    def reset_filters(self):
        self.year_var.set("")
        self.month_var.set("")
        self.category_var.set("")
        self.filtered_data = self.data.copy()
        self.update_table()

    def apply_filters(self):
        y, m, c = self.year_var.get(), self.month_var.get(), self.category_var.get()
        self.filtered_data = [
            d for d in self.data
            if (not y or d["date"].startswith(y)) and
               (not m or d["date"][5:7] == m) and
               (not c or d["category"] == c)
        ]
        self.update_table()

    def sort_by_column(self, col):
        key_map = {
            "Дата": "date", "UZS": "uzs", "USD": "usd", "Курс": "rate",
            "Итог в UZS": "total_uzs", "Категория": "category", "Комментарий": "comment"
        }
        key = key_map.get(col, col)
        self.filtered_data.sort(key=lambda x: str(x.get(key, "")), reverse=self.sort_reverse)
        self.sort_reverse = not self.sort_reverse
        self.update_table()

    def update_table(self):
        self.tree.delete(*self.tree.get_children())
        total = 0
        per_cat = {}
        for i, d in enumerate(self.filtered_data):
            total += d["total_uzs"]
            per_cat[d["category"]] = per_cat.get(d["category"], 0) + d["total_uzs"]
            self.tree.insert("", "end", iid=i, values=(
                d["date"], d["uzs"], d["usd"], d["rate"],
                f'{d["total_uzs"]:,}'.replace(",", " "),
                d["category"], d.get("comment", "")
            ))
        text = f"ИТОГО (всего): {total:,} сум".replace(",", " ")
        for cat, val in per_cat.items():
            text += f"\n{cat}: {val:,}".replace(",", " ")
        self.total_label.config(text=text)

    def add_record(self):
        dialog = RecordDialog(self, self.categories)
        self.wait_window(dialog)
        if dialog.result:
            self.data.append(dialog.result)
            if dialog.result["category"] not in self.categories:
                self.categories.append(dialog.result["category"])
            self.save_all()
            self.filtered_data = self.data.copy()
            self.update_filter_options()
            self.update_table()

    def edit_record(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        record = self.filtered_data[idx]
        original_idx = self.data.index(record)
        dialog = RecordDialog(self, self.categories, record)
        self.wait_window(dialog)
        if dialog.result:
            self.data[original_idx] = dialog.result
            if dialog.result["category"] not in self.categories:
                self.categories.append(dialog.result["category"])
            self.save_all()
            self.filtered_data = self.data.copy()
            self.update_filter_options()
            self.update_table()

    def delete_record(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        record = self.filtered_data[idx]
        if messagebox.askyesno("Удалить", "Удалить выбранную запись?"):
            self.data.remove(record)
            self.save_all()
            self.filtered_data = self.data.copy()
            self.update_table()

    def export_to_excel(self):
        if not self.filtered_data:
            return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx")
        if not path:
            return
        pd.DataFrame(self.filtered_data).to_excel(path, index=False)
        messagebox.showinfo("Готово", f"Данные экспортированы в: {path}")

    def plot_data(self):
        if not self.filtered_data:
            return
        df = pd.DataFrame(self.filtered_data)
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)

        try:
            monthly_total = df.resample("M").sum(numeric_only=True)
            by_category = df.groupby("category").sum(numeric_only=True)

            win = tk.Toplevel(self)
            win.title("Графики")
            win.geometry("1000x500")

            # --- График по месяцам ---
            fig1, ax1 = plt.subplots(figsize=(5, 3))
            monthly_total["total_uzs"].plot(kind="bar", ax=ax1)
            ax1.set_title("Доходы по месяцам")
            ax1.set_ylabel("Сумма (UZS)")
            ax1.set_xlabel("Месяц")
            ax1.tick_params(axis="x", rotation=45)
            ax1.ticklabel_format(style='plain', axis='y')
            fig1.tight_layout()

            # --- График по категориям ---
            fig2, ax2 = plt.subplots(figsize=(5, 3))
            by_category["total_uzs"].plot(kind="bar", ax=ax2, color="gray")
            ax2.set_title("По категориям")
            ax2.set_ylabel("Сумма (UZS)")
            ax2.set_xlabel("Категория")
            ax2.tick_params(axis="x", rotation=45)
            ax2.ticklabel_format(style='plain', axis='y')
            fig2.tight_layout()

            # --- Отображение в окне ---
            canvas1 = FigureCanvasTkAgg(fig1, master=win)
            canvas1.draw()
            canvas1.get_tk_widget().pack(side="left", fill="both", expand=True)

            canvas2 = FigureCanvasTkAgg(fig2, master=win)
            canvas2.draw()
            canvas2.get_tk_widget().pack(side="right", fill="both", expand=True)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при построении графика: {e}")

    def show_details(self, event):
        item_id = self.tree.selection()
        if not item_id:
            return
        idx = int(item_id[0])
        record = self.filtered_data[idx]

        field_names = {
            "date": "Дата",
            "usd": "USD",
            "uzs": "UZS",
            "rate": "Курс",
            "total_uzs": "Итог в UZS",
            "category": "Категория",
            "comment": "Комментарий"
        }

        lines = [f"{field_names.get(k, k)}: {v}" for k, v in record.items()]
        messagebox.showinfo("Детали записи", "\n".join(lines))

class RecordDialog(tk.Toplevel):
    def __init__(self, parent, categories, data=None):
        super().__init__(parent)
        self.title("Добавить / Редактировать запись")
        self.geometry("400x420")
        self.result = None
        self.categories = categories

        self.bind("<Return>", lambda e: self.on_save())
        self.bind("<Escape>", lambda e: self.destroy())

        self.date_var = tk.StringVar(value=data["date"] if data else datetime.today().strftime("%Y-%m-%d"))
        self.uzs_var = tk.StringVar(value=str(data["uzs"]) if data else "")
        self.usd_var = tk.StringVar(value=str(data["usd"]) if data else "")
        self.rate_var = tk.StringVar(value=str(data["rate"]) if data else "")
        self.category_var = tk.StringVar(value=data["category"] if data else "")
        self.comment_var = tk.StringVar(value=data.get("comment", "") if data else "")

        self.init_ui()

    def init_ui(self):
        padding = {"padx": 10, "pady": 4}

        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        frame = ttk.Frame(canvas)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)

        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0, 0), window=frame, anchor="nw")
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        for label, var in [
            ("Дата", self.date_var),
            ("Сумма в UZS", self.uzs_var),
            ("Сумма в USD", self.usd_var),
            ("Курс USD", self.rate_var),
            ("Категория", self.category_var),
            ("Комментарий", self.comment_var)
        ]:
            ttk.Label(frame, text=label).pack(**padding)

            if label == "Дата":
                self.date_entry = DateEntry(frame, textvariable=var, date_pattern="yyyy-mm-dd")
                self.date_entry.pack(fill="x", **padding)
            elif label == "Категория":
                self.cat_box = ttk.Combobox(frame, textvariable=var, values=self.categories)
                self.cat_box.pack(fill="x", **padding)
            else:
                ttk.Entry(frame, textvariable=var).pack(fill="x", **padding)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Сохранить", command=self.on_save).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Отмена", command=self.destroy).pack(side="left", padx=10)



    def on_save(self):
        try:
            usd = float(self.usd_var.get() or 0)
            uzs = float(self.uzs_var.get() or 0)
            rate = float(self.rate_var.get() or 0)
            if usd and not rate:
                messagebox.showwarning("Ошибка", "Введите курс для USD")
                return
            total = int(usd * rate + uzs)
            if usd > 0 and not self.category_var.get():
                for c in self.categories:
                    if "USD" in c:
                        self.category_var.set(c)
                        break
            self.result = {
                "date": self.date_var.get(),
                "usd": usd,
                "uzs": uzs,
                "rate": rate,
                "total_uzs": total,
                "category": self.category_var.get().strip(),
                "comment": self.comment_var.get().strip()
            }
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка ввода: {e}")

if __name__ == "__main__":
    app = FinanceTracker()
    app.mainloop()
