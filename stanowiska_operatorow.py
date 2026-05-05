import os
import json
import datetime
import tkinter as tk
from tkinter import ttk, messagebox

PLIK_STANOWISK = "stanowiska_operatorow.json"
PLIK_POTWIERDZEN = "potwierdzenia_narzedzi_stanowisk.json"


def _czas():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _nazwa(x):
    if isinstance(x, dict):
        return str(x.get("name", "")).strip()
    return str(x).strip()


def _unikalne(lista):
    wynik = []
    widziane = set()
    for x in lista or []:
        n = _nazwa(x)
        if n and n.lower() not in widziane:
            widziane.add(n.lower())
            wynik.append(n)
    return wynik


def _czytaj(path, default):
    try:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8-sig") as f:
                return json.load(f)
    except Exception:
        pass
    return default


def _zapisz(path, dane):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig") as f:
        json.dump(dane, f, ensure_ascii=False, indent=2)


class ZakladkaStanowisk(ttk.Frame):
    def __init__(self, master, narzedzia=None, operatorzy=None, folder_danych=None):
        super().__init__(master, padding=8)
        self.folder_danych = folder_danych or os.getcwd()
        self.plik_stanowisk = os.path.join(self.folder_danych, PLIK_STANOWISK)
        self.plik_potwierdzen = os.path.join(self.folder_danych, PLIK_POTWIERDZEN)
        self.narzedzia = _unikalne(narzedzia)
        self.operatorzy = _unikalne(operatorzy)
        self.widgets = {}
        self.dane = self._wczytaj_stanowiska()
        self._buduj()
        self.odswiez()

    def _wczytaj_stanowiska(self):
        domyslne = {"stanowiska": []}
        for i in range(1, 7):
            domyslne["stanowiska"].append({"id": f"ST-{i:02d}", "narzedzia": [], "ostatnie_potwierdzenie": {}})
        dane = _czytaj(self.plik_stanowisk, domyslne)
        if not isinstance(dane, dict):
            dane = domyslne
        if not isinstance(dane.get("stanowiska"), list):
            dane["stanowiska"] = []
        while len(dane["stanowiska"]) < 6:
            i = len(dane["stanowiska"]) + 1
            dane["stanowiska"].append({"id": f"ST-{i:02d}", "narzedzia": [], "ostatnie_potwierdzenie": {}})
        dane["stanowiska"] = dane["stanowiska"][:6]
        return dane

    def _zapisz_stanowiska(self):
        self.dane["aktualizacja"] = _czas()
        _zapisz(self.plik_stanowisk, self.dane)

    def _buduj(self):
        gora = ttk.Frame(self)
        gora.pack(fill="x", pady=(0, 8))
        ttk.Label(gora, text="Stanowiska operatorskie - narzędzia pomiarowe", font=("Segoe UI", 12, "bold")).pack(side="left")
        ttk.Button(gora, text="Zapisz", command=self.zapisz).pack(side="right", padx=4)
        ttk.Button(gora, text="Odśwież", command=self.odswiez).pack(side="right", padx=4)

        opis = "Na każdym stanowisku można przypisać narzędzia pomiarowe. Operator potwierdza obecność i sprawność narzędzi."
        ttk.Label(self, text=opis, wraplength=1100).pack(fill="x", pady=(0, 8))

        siatka = ttk.Frame(self)
        siatka.pack(fill="both", expand=True)
        for i in range(6):
            self._karta(siatka, i, i // 2, i % 2)
        siatka.columnconfigure(0, weight=1)
        siatka.columnconfigure(1, weight=1)

    def _karta(self, parent, idx, row, col):
        ramka = ttk.LabelFrame(parent, text=f"Stanowisko {idx + 1}", padding=8)
        ramka.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
        ramka.columnconfigure(1, weight=1)

        id_var = tk.StringVar()
        narz_var = tk.StringVar()
        oper_var = tk.StringVar()
        stan_var = tk.StringVar(value="Sprawne")
        uwagi_var = tk.StringVar()
        ostatnie_var = tk.StringVar(value="Ostatnie potwierdzenie: brak")

        ttk.Label(ramka, text="ID stanowiska:").grid(row=0, column=0, sticky="w")
        ttk.Entry(ramka, textvariable=id_var).grid(row=0, column=1, sticky="ew", padx=4)

        ttk.Label(ramka, text="Narzędzie:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        cb_n = ttk.Combobox(ramka, textvariable=narz_var, values=self.narzedzia, state="readonly")
        cb_n.grid(row=1, column=1, sticky="ew", padx=4, pady=(6, 0))

        lista = tk.Listbox(ramka, height=6, exportselection=False)
        lista.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=6)

        przyciski = ttk.Frame(ramka)
        przyciski.grid(row=3, column=0, columnspan=2, sticky="ew")
        ttk.Button(przyciski, text="Dodaj", command=lambda: self.dodaj_narzedzie(idx)).pack(side="left", padx=(0, 4))
        ttk.Button(przyciski, text="Usuń", command=lambda: self.usun_narzedzie(idx)).pack(side="left")

        ttk.Separator(ramka).grid(row=4, column=0, columnspan=2, sticky="ew", pady=8)

        ttk.Label(ramka, text="Operator:").grid(row=5, column=0, sticky="w")
        ttk.Combobox(ramka, textvariable=oper_var, values=self.operatorzy, state="readonly").grid(row=5, column=1, sticky="ew", padx=4)

        ttk.Label(ramka, text="Stan:").grid(row=6, column=0, sticky="w", pady=(6, 0))
        ttk.Combobox(ramka, textvariable=stan_var, values=["Sprawne", "Brak lub niesprawne"], state="readonly").grid(row=6, column=1, sticky="ew", padx=4, pady=(6, 0))

        ttk.Label(ramka, text="Uwagi:").grid(row=7, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(ramka, textvariable=uwagi_var).grid(row=7, column=1, sticky="ew", padx=4, pady=(6, 0))

        ttk.Label(ramka, textvariable=ostatnie_var).grid(row=8, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Button(ramka, text="Potwierdź narzędzia", command=lambda: self.potwierdz(idx)).grid(row=9, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        self.widgets[idx] = {"id": id_var, "narz": narz_var, "lista": lista, "oper": oper_var, "stan": stan_var, "uwagi": uwagi_var, "ostatnie": ostatnie_var}

    def _sync_id(self, idx):
        st = self.dane["stanowiska"][idx]
        st["id"] = self.widgets[idx]["id"].get().strip() or f"ST-{idx + 1:02d}"

    def odswiez(self):
        for i, st in enumerate(self.dane["stanowiska"]):
            w = self.widgets[i]
            w["id"].set(st.get("id", f"ST-{i + 1:02d}"))
            w["lista"].delete(0, tk.END)
            for n in st.get("narzedzia", []):
                w["lista"].insert(tk.END, n)
            p = st.get("ostatnie_potwierdzenie", {})
            if isinstance(p, dict) and p.get("czas"):
                w["ostatnie"].set(f"Ostatnie potwierdzenie: {p.get('czas')} | {p.get('operator')} | {p.get('stan')}")
            else:
                w["ostatnie"].set("Ostatnie potwierdzenie: brak")

    def dodaj_narzedzie(self, idx):
        self._sync_id(idx)
        nazwa = self.widgets[idx]["narz"].get().strip()
        if not nazwa:
            messagebox.showwarning("Narzędzie", "Wybierz narzędzie do dodania.")
            return
        lista = self.dane["stanowiska"][idx].setdefault("narzedzia", [])
        if nazwa not in lista:
            lista.append(nazwa)
        self._zapisz_stanowiska()
        self.odswiez()

    def usun_narzedzie(self, idx):
        zazn = self.widgets[idx]["lista"].curselection()
        if not zazn:
            messagebox.showwarning("Narzędzie", "Zaznacz narzędzie do usunięcia.")
            return
        self._sync_id(idx)
        nazwa = self.widgets[idx]["lista"].get(zazn[0])
        self.dane["stanowiska"][idx]["narzedzia"] = [x for x in self.dane["stanowiska"][idx].get("narzedzia", []) if x != nazwa]
        self._zapisz_stanowiska()
        self.odswiez()

    def potwierdz(self, idx):
        self._sync_id(idx)
        w = self.widgets[idx]
        operator = w["oper"].get().strip()
        if not operator:
            messagebox.showwarning("Operator", "Wybierz operatora.")
            return
        st = self.dane["stanowiska"][idx]
        wpis = {"czas": _czas(), "stanowisko_id": st.get("id"), "operator": operator, "stan": w["stan"].get(), "uwagi": w["uwagi"].get().strip(), "narzedzia": list(st.get("narzedzia", []))}
        st["ostatnie_potwierdzenie"] = wpis
        self._zapisz_stanowiska()
        historia = _czytaj(self.plik_potwierdzen, [])
        if not isinstance(historia, list):
            historia = []
        historia.append(wpis)
        _zapisz(self.plik_potwierdzen, historia)
        self.odswiez()
        messagebox.showinfo("Potwierdzenie", "Zapisano potwierdzenie operatora.")

    def zapisz(self):
        for i in range(6):
            self._sync_id(i)
        self._zapisz_stanowiska()
        messagebox.showinfo("Zapis", "Zapisano stanowiska.")


def dodaj_zakladke_stanowisk(notebook, app=None, narzedzia=None, operatorzy=None, folder_danych=None):
    if app is not None:
        narzedzia = narzedzia if narzedzia is not None else getattr(app, "narzedzia", [])
        operatorzy = operatorzy if operatorzy is not None else getattr(app, "operatorzy", [])
        folder_danych = folder_danych if folder_danych is not None else getattr(app, "folder_danych", None)
    tab = ZakladkaStanowisk(notebook, narzedzia=narzedzia, operatorzy=operatorzy, folder_danych=folder_danych)
    notebook.add(tab, text="Stanowiska")
    return tab
