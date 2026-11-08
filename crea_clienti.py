import os
import numpy as np
import pandas as pd

generatore_casuale = np.random.default_rng(42) #seed fisso a 42
OGGI = pd.Timestamp("2026-11-05") #data in formato internazionale perché pandas se no in formato italiano inverte mesi/giorni
PREZZI_PIANI = {"Gratis": 0, "Basic": 10, "Family": 25} #prezzo mensile

#profilo del cliente (numero di clienti, n giorni da quanto sono iscritti, probabilità del piano gratis/basic/family,
#media di accessi con deviazione standard, giorni passati dall'ultimo accesso, probabilità della categoria di servizio preferita musica/podcast/audiolibri)
PROFILI_CLIENTI = {
"Frequente": (100, (120, 366), [0.10, 0.60, 0.30], (55, 10), (0, 7), [0.60, 0.25, 0.15]),
"Inattivo": (110, (150, 366), [0.50, 0.40, 0.10], (4, 2), (40, 121), [0.40, 0.30, 0.30]),
"Occasionale": (150, (90, 366), [0.30, 0.55, 0.15], (18, 6), (5,31), [0.40, 0.40, 0.20]),
"Recente": (90, (1, 46), [0.50, 0.40, 0.10], (6, 3), (0, 11), [0.45, 0.35, 0.20]),
}

#crea una tabella vuota in cui si aggiunge un profilo cliente alla volta
tabella_clienti = pd.DataFrame()
for profilo, (n, iscritto, probabilita_piano, accessi, ultimo_accesso, probabilita_categoria) in PROFILI_CLIENTI.items():
    giorni_iscritto = generatore_casuale.integers(iscritto[0], iscritto[1], n)
    zona = generatore_casuale.choice(["Nord", "Centro", "Sud", "Isole"], n, p=[0.4, 0.25, 0.25, 0.1])
    piano = generatore_casuale.choice(list(PREZZI_PIANI), n, p=probabilita_piano) 
    n_accessi = generatore_casuale.normal(accessi[0], accessi[1], n).clip(0).round()
    giorni_ultimo_accesso = np.minimum(generatore_casuale.integers(ultimo_accesso[0], ultimo_accesso[1], n), giorni_iscritto)
    categoria_preferita = generatore_casuale.choice(["Musica", "Podcast", "Audiolibri"], n, p=probabilita_categoria)

    prezzo = ([PREZZI_PIANI[p] for p in piano]) #prezzo mensile del piano del cliente
    mesi_pagati = np.ceil(giorni_iscritto / 30) #mesi di iscrizione arrotondati per eccesso
    mesi_pagati = mesi_pagati.clip(max=3) #imposta 3 pagamenti max in 3 mesi (lasso di tempo per l'importo totale speso)
    nuovi_clienti = pd.DataFrame({
    "Zona": zona,
    "Data_iscrizione": [OGGI - pd.Timedelta(days=int(giorni)) for giorni in giorni_iscritto], #calcolo data iscrizione
    "Piano": piano,
    "Accessi_90gg": n_accessi,
    "Giorni_ultimo_accesso": giorni_ultimo_accesso,
    "Categoria_preferita": categoria_preferita,
    "Importo_totale_90gg": prezzo * mesi_pagati,
    "Profilo_simulato": profilo, #profilo del cliente inventato (il clustering non lo usa)
    })
    tabella_clienti = pd.concat([tabella_clienti, nuovi_clienti], ignore_index=True) #aggiunge i clienti nuovi sotto a quelli generati

#mescola le righe della tabella, così i profili uguali non restano in blocchi
tabella_clienti = tabella_clienti.sample(frac=1, random_state=42)
tabella_clienti = tabella_clienti.reset_index(drop=True)

#crea un codice anonimo per ogni cliente, CC (codice cliente) + numeri progressivi da 0001
codice_cliente = []
for numero in range(1, len(tabella_clienti) + 1):
    codice_cliente.append("CC" + str(numero).zfill(4))
tabella_clienti.insert(0, "ID_cliente", codice_cliente)

#genera valori mancanti (12 valori mancanti in 2 colonne diverse)
generatore_valori_mancanti = np.random.default_rng(42)
for colonna in ["Accessi_90gg", "Giorni_ultimo_accesso"]:
    righe_da_svuotare = generatore_valori_mancanti.choice(len(tabella_clienti), 12, replace=False)
    tabella_clienti.loc[righe_da_svuotare, colonna] = np.nan

os.makedirs("dati", exist_ok=True)  #crea la cartella dati se non esiste
tabella_clienti.to_csv("dati/clienti.csv", index=False)

