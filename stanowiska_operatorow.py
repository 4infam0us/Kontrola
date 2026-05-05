import os
import json
import datetime
import socket
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


def _pobierz_narzedzia_z_app(app, narzedzia=None):
    if narzedzia is not None:
        return _unikalne(narzedzia)
    if app is None:
        return []
    for attr in ("narzedzia", "tools", "lista_narzedzi"):
        wartosc = getattr(app, attr, None)
        if wartosc:
            return _unikalne(wartosc)
    return []


def _pobierz_operatorow_z_app(app, operatorzy=None):
    if operatorzy is not None:
        return _unikalne(operatorzy)
    if app is None:
        return []
    for attr in ("operatorzy", "operators", "lista_operatorow"):
        wartosc = getattr(app, attr, None)
        if wartosc:
            return _unikalne(wartosc)
    return []


def _pobierz_folder_danych_z_app(app, folder_danych=None):
    if folder_danych:
        return folder_danych
    if app is None:
        return os.getcwd()
    for attr in ("folder_danych", "data_folder", "katalog_danych"):
        wartosc = getattr(app, attr, None)
        if wartosc:
            return wartosc
    return os.getcwd()


def _pobierz_stanowisko_z_app(app):
    if app is None:
        return socket.gethostname()
    for attr in ("stanowisko_id", "station_id", "stanowisko", "current_station_id"):
        wartosc = getattr(app, attr, None)
        if wartosc:
            return str(wartosc).strip()
    return socket.gethostname()


class ZakladkaStanowisk(ttk.Frame):
    def __init__(self, master, app=None, narzedzia=None, operatorzy=None, folder_danych=None):
        super().__init__(master, padding=8)
        self.app = app
        self.folder_danych = _pobierz_folder_danych_z_app(app, folder_danych)
        self.plik_stanowisk = os.path.join(self.folder_danych, PLIK_STANOWISK)
        self.plik_potwierdzen = os.path.join(self.folder_danych, PLIK_POTWIERDZEN)
        self.narzedzia = _pobierz_narzedzia_z_app(app, narzedzia)
        self.operatorzy = _pobierz_operatorow_z_app(app, operatorzy)
        self.aktywne_stanowisko_id = _pobierz_stanowisko_z_app(app)
        self.widgets = {}
        self.dane = self._wczytaj_stanowiska()
        self._buduj()
        self.odswiez()

    def odswiez_z_programu(self):
        self.narzedzia = _pobierz_narzedzia_z_app(self.app, None)
        self.operatorzy = _pobierz_operatorow_z_app(self.app, None)
        self.aktywne_stanowisko_id = _pobierz_stanowisko_z_app(self.app)
        for w in self.widgets.values():
            if "cb_narz" in w:
                w["cb_narz"]["values"] = self.narzedzia
            if "cb_oper" in w:
                w["cb_oper"]["values"] = self.operatorzy
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

    def _znajdz_stanowisko(self, stanowisko_id=None):
        sid = (stanowisko_id or self.aktywne_stanowisko_id or "").strip()
        for i, st in enumerate(self.dane["stanowiska"]):
            if str(st.get("id", "")).strip().lower() == sid.lower():
                return i, st
        return None, None

    def _buduj(self):
        gora = ttk.Frame(self)
        gora.pack(fill="x", pady=(0, 8))
        ttk.Label(gora, text="Stanowiska operatorskie - narzędzia pomiarowe", font=("Segoe UI", 12, "bold")).pack(side="left")
        ttk.Button(gora, text="Zapisz", command=self.zapisz).pack(side="right", padx=4)
        ttk.Button(gora, text="Odśwież z programu", command=self.odswiez_z_programu).pack(side="right", padx=4)

        ttk.Label(self, text="Narzędzia z list rozwijanych są pobierane z centralnej listy programu: Narzędzia pomiarowe / Zarządzanie. ID stanowisk powinny odpowiadać konfiguracji stanowiska w programie.", wraplength=1100).pack(fill="x", pady=(0, 8))

        self.lbl_aktywne = ttk.Label(self, text="", font=("Segoe UI", 10, "bold"))
        self.lbl_aktywne.pack(fill="x", pady=(0, 8))

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

        ttk.Label(ramka, text="Narzędzie z programu:").grid(row=1, column=0, sticky="w", pady=(6, 0))
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
        cb_oper = ttk.Combobox(ramka, textvariable=oper_var, values=self.operatorzy, state="readonly")
        cb_oper.grid(row=5, column=1, sticky="ew", padx=4)

        ttk.Label(ramka, text="Stan:").grid(row=6, column=0, sticky="w", pady=(6, 0))
        ttk.Combobox(ramka, textvariable=stan_var, values=["Sprawne", "Brak lub niesprawne"], state="readonly").grid(row=6, column=1, sticky="ew", padx=4, pady=(6, 0))

        ttk.Label(ramka, text="Uwagi:").grid(row=7, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(ramka, textvariable=uwagi_var).grid(row=7, column=1, sticky="ew", padx=4, pady=(6, 0))

        ttk.Label(ramka, textvariable=ostatnie_var).grid(row=8, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Button(ramka, text="Potwierdź narzędzia", command=lambda: self.potwierdz(idx)).grid(row=9, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        self.widgets[idx] = {"id": id_var, "narz": narz_var, "cb_narz": cb_n, "lista": lista, "oper": oper_var, "cb_oper": cb_oper, "stan": stan_var, "uwagi": uwagi_var, "ostatnie": ostatnie_var}

    def _sync_id(self, idx):
        st = self.dane["stanowiska"][idx]
        st["id"] = self.widgets[idx]["id"].get().strip() or f"ST-{idx + 1:02d}"

    def odswiez(self):
        self.lbl_aktywne.config(text=f"Aktywne stanowisko z konfiguracji programu: {self.aktywne_stanowisko_id}")
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
            messagebox.showwarning("Narzędzie", "Wybierz narzędzie z listy Narzędzia pomiarowe / Zarządzanie.")
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

    def potwierdz(self, idx, operator=None, stan=None, uwagi=None):
        self._sync_id(idx)
        w = self.widgets[idx]
        operator = (operator or w["oper"].get()).strip()
        if not operator:
            messagebox.showwarning("Operator", "Wybierz operatora.")
            return False
        st = self.dane["stanowiska"][idx]
        wpis = {"czas": _czas(), "stanowisko_id": st.get("id"), "operator": operator, "stan": stan or w["stan"].get(), "uwagi": uwagi if uwagi is not None else w["uwagi"].get().strip(), "narzedzia": list(st.get("narzedzia", []))}
        st["ostatnie_potwierdzenie"] = wpis
        self._zapisz_stanowiska()
        historia = _czytaj(self.plik_potwierdzen, [])
        if not isinstance(historia, list):
            historia = []
        historia.append(wpis)
        _zapisz(self.plik_potwierdzen, historia)
        self.odswiez()
        messagebox.showinfo("Potwierdzenie", "Zapisano potwierdzenie operatora.")
        return True

    def potwierdz_aktywne_stanowisko(self, operator, stan="Sprawne", uwagi=""):
        self.odswiez_z_programu()
        idx, st = self._znajdz_stanowisko(self.aktywne_stanowisko_id)
        if st is None:
            messagebox.showerror("Stanowisko", f"Nie znaleziono stanowiska '{self.aktywne_stanowisko_id}' w zakładce Stanowiska. Uzupełnij ID stanowiska zgodnie z konfiguracją programu.")
            return False
        return self.potwierdz(idx, operator=operator, stan=stan, uwagi=uwagi)

    def zapisz(self):
        for i in range(6):
            self._sync_id(i)
        self._zapisz_stanowiska()
        messagebox.showinfo("Zapis", "Zapisano stanowiska.")


def dodaj_zakladke_stanowisk(notebook, app=None, narzedzia=None, operatorzy=None, folder_danych=None):
    tab = ZakladkaStanowisk(notebook, app=app, narzedzia=narzedzia, operatorzy=operatorzy, folder_danych=folder_danych)
    notebook.add(tab, text="Stanowiska")
    if app is not None:
        setattr(app, "tab_stanowiska", tab)
    return tab


def dodaj_potwierdzenie_stanowiska_do_pomiarow(parent, app, operator_var=None):
    ramka = ttk.LabelFrame(parent, text="Potwierdzenie narzędzi na stanowisku", padding=8)
    ramka.pack(fill="x", padx=8, pady=8)
    lbl = ttk.Label(ramka, text=f"Stanowisko z konfiguracji: {_pobierz_stanowisko_z_app(app)}")
    lbl.pack(side="left", padx=(0, 12))

    def _operator():
        if operator_var is not None:
            try:
                return operator_var.get().strip()
            except Exception:
                pass
        for attr in ("operator_var", "var_operator", "selected_operator"):
            v = getattr(app, attr, None)
            if hasattr(v, "get"):
                return v.get().strip()
            if isinstance(v, str):
                return v.strip()
        return ""

    def _potwierdz():
        operator = _operator()
        if not operator:
            messagebox.showwarning("Operator", "Najpierw wybierz operatora w zakładce Pomiary.")
            return
        tab = getattr(app, "tab_stanowiska", None)
        if tab is None:
            messagebox.showerror("Stanowiska", "Najpierw dodaj zakładkę Stanowiska do programu.")
            return
        tab.potwierdz_aktywne_stanowisko(operator)

    ttk.Button(ramka, text="Potwierdź obecność i sprawność narzędzi", command=_potwierdz).pack(side="left")
    return ramka
