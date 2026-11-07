import math
import pandas as pd
import streamlit as st


OGGI= pd.Timestamp("2026-11-05")
PREZZI_PIANI= {"Gratis": 0, "Basic": 10, "Family": 25}
#le tre variabili usate per formare i gruppi di clienti
VARIABILI=["Accessi_90gg", "Importo_totale_90gg", "Giorni_ultimo_accesso"]

#tipo di offerta da proporre al cliente in base al gruppo in cui si trova
OFFERTE = {
"Famiglie attive": "Per tenerli ill piu' a lungo possibile proponiamo l'abbonamento annuale scontato: 12 mesi al rezzo di 10.",
"Famiglie meno attive": "Un mese di Family a 20€ invece di 25€, con un profilo extra per un altro familiare, per invogliare lútilizzo del servizio.",
"Attivi con piano base": "Usano molto il servizio, quindi proponiamo il piano family per i primi due mesi a 15€ invece di 25€.",
#usano il servizio poco e spendono poco, sono clienti occasionali o iscritti da poco
"Intermedi e nuovi": "Ai clienti con piano Gratis proponiamo il 1° mese di Basic a 5€ invece di 10€ per far provare i vantaggi del servizio. ",
#clienti che non entrano da molto tempo, alcuni hanno un abbonamento mentre altri utilizzano il piano Gratis
"Inattivi": "Ai clienti Basic proponiamo tre mesi a 5€ invece di 10€ per farli tornare attivi. Ai clienti con piano Gratis offriamo un mese di piano Basic gratuito."
}

st.set_page_config (page_title="MusicBeat", layout="wide")
st.title ("MusicBeat")
st.header ("Segmentazione dei clienti")


clienti_segmentati= pd.read_csv("dati/clienti_segmentati.csv", parse_dates=["Data_iscrizione"])


if "clienti_aggiunti" not in st.session_state:
    st.session_state["clienti_aggiunti"]= []

#tabelli dei clienti originali + quelli aggiuntui
tabella_clienti= clienti_segmentati
if len (st.session_state ["clienti_aggiunti"]) > 0:
    clienti_nuovi= pd.DataFrame(st.session_state["clienti_aggiunti"])
    tabella_clienti= pd.concat ([clienti_segmentati, clienti_nuovi], ignore_index=True)

def trova_gruppo(accessi, importo, giorni):
    #trova il gruppo a cui assomiglia di piu iol nuovo cliente.
    clienti_standardizzati = clienti_segmentati[VARIABILI].copy()
    nuovo_cliente = {"Accessi_90gg": accessi, "Importo_totale_90gg": importo, "Giorni_ultimo_accesso": giorni}

    #standardizzo ogni variabile dei clienti con la stessa media e deviazione
    for variabile in VARIABILI:
        media= clienti_segmentati[variabile].mean()
        deviazione = clienti_segmentati[variabile].std(ddof=0)
        clienti_standardizzati [variabile]= (clienti_segmentati[variabile] -media) /deviazione
        nuovo_cliente [variabile]= (nuovo_cliente[variabile] - media) / deviazione

    #il centro di un gruppo è la media dei valori delle variabili dei suoi clienti
    clienti_standardizzati["Nome_gruppo"] = clienti_segmentati["Nome_gruppo"]
    centri = clienti_standardizzati.groupby("Nome_gruppo").mean()

    #cerco il gruppo con la distanza più piccola dal nuovo cliente
    distanza_minima = None
    for nome_gruppo in clienti_segmentati["Nome_gruppo"].unique():
        distanza =0
        for variabile in VARIABILI:
            #usato esponente al quadrato per eliminare il problema del segno positivo/negativop
            distanza = distanza + (centri[variabile][nome_gruppo] - nuovo_cliente[variabile]) ** 2
        if distanza_minima is None or distanza < distanza_minima:
            distanza_minima = distanza
            gruppo_vicino = nome_gruppo
    return gruppo_vicino


#imposto i filtri
st.subheader("Filtri")
col1, col2, col3, col4= st.columns(4)
zona= col1.selectbox ("Zona", ["Tutte"] + sorted(tabella_clienti ["Zona"].unique()))
categoria= col2.selectbox("Categoria preferita", ["Tutte"] + sorted(tabella_clienti["Categoria_preferita"] .unique()))
data_dal= col3.date_input("Iscritti dal", tabella_clienti ["Data_iscrizione"] .min())
data_al= col4.date_input("Iscritti fino al", tabella_clienti ["Data_iscrizione"] .max())
                         


#vengono applicati i filtri scelti da''utente
clienti_filtrati= tabella_clienti[tabella_clienti["Data_iscrizione"] >= pd.Timestamp(data_dal)]
clienti_filtrati= clienti_filtrati[clienti_filtrati["Data_iscrizione"] <= pd.Timestamp(data_al)]
if zona != "Tutte":
    clienti_filtrati= clienti_filtrati[clienti_filtrati["Zona"] ==zona]
if categoria != "Tutte":
    clienti_filtrati= clienti_filtrati[clienti_filtrati["Categoria_preferita"] ==categoria]

st.write (f"**Clienti selezionati:** {len(clienti_filtrati)} su {len(tabella_clienti)}" )
if len(clienti_filtrati) == 0:
    st.warning("Nessun cliente corrisponde ai filtri scelti.")
    st.stop()  # evita che esca errore per una tabella vuota


#grafico a dispersione
st.scatter_chart(clienti_filtrati, x= "Giorni_ultimo_accesso", y= "Accessi_90gg", color= "Nome_gruppo", x_label= "Giorni dall'ultimo accesso", y_label= "Accessi negli ultimi 90 giorni")


#tabella dei profili dei clienti
medie_gruppi= clienti_filtrati.groupby("Nome_gruppo")[VARIABILI] .mean()
profilo_gruppi= medie_gruppi.round(0) .astype(int)
profilo_gruppi.columns= ["Accessi (media 90 gg)", "Spesa media (€)", "Giorni dall'ultimo accesso"]
profilo_gruppi["Clienti"] = clienti_filtrati["Nome_gruppo"].value_counts()

#clienti come prima colonna e ordino dal gruppo più numeroso
profilo_gruppi = profilo_gruppi[["Clienti", "Accessi (media 90 gg)", "Spesa media (€)", "Giorni dall'ultimo accesso"]]
profilo_gruppi = profilo_gruppi.sort_values("Clienti", ascending=False)
profilo_gruppi.index.name = "Gruppo"

st.subheader("Profilo dei gruppi")
st.table(profilo_gruppi)

#offerte proposte
st.subheader("Offerta da proporre a ciascun gruppo")
for nome_gruppo in OFFERTE:
    st.write(f"**{nome_gruppo}:** {OFFERTE [nome_gruppo]}")


st.subheader ("Nuovo cliente")
# essaggio di conferma dopo aver aggiunto un cliente
if "messaggio" in st.session_state:
    st.success(st.session_state.pop("messaggio"))

#inserimento nuovo cliente
data_iniziale = (OGGI - pd.Timedelta(days=100)) .date()  # data impostata all'apertura della selezione
opzioni_piano= ["Gratis", "Basic", "Family"]
opzioni_zona= sorted(clienti_segmentati["Zona"].unique())
opzioni_categoria= sorted(clienti_segmentati["Categoria_preferita"].unique())
 
with st.form("nuovo_cliente"):
    colonna_sinistra, colonna_destra= st.columns(2)
    accessi= colonna_sinistra.number_input("Accessi negli ultimi 90 giorni", 0, 200, 20)
    giorni_ultimo_accesso= colonna_sinistra.number_input("Giorni dall'ultimo accesso", 0, 365, 10)
    data_iscrizione= colonna_sinistra.date_input("Data di iscrizione", data_iniziale, max_value=OGGI.date())
    piano= colonna_destra.selectbox("Piano", opzioni_piano)
    zona_nuovo = colonna_destra.selectbox("Zona del nuovo cliente", opzioni_zona)
    categoria_nuovo= colonna_destra.selectbox("Categoria del nuovo cliente", opzioni_categoria)
    pulsante_trova= st.form_submit_button("Trova il gruppo")
    pulsante_aggiungi = st.form_submit_button("Aggiungi ai clienti")

if pulsante_trova or pulsante_aggiungi:

    #controllo dei dati e calcolo dell'importo del piano
    giorni_iscritto= (OGGI - pd.Timestamp(data_iscrizione)).days
    mesi_pagati= math.ceil(giorni_iscritto / 30)  #un mese iniziato conta come pagato, ipotizzando che l'addebito arrivi al 1°giorno del mese
    if mesi_pagati > 3:
        mesi_pagati = 3  #ho tenuro 3 mesi (90gg) come finestra di analisi dei dati
    importo= PREZZI_PIANI [piano] * mesi_pagati
 
    if giorni_ultimo_accesso > giorni_iscritto:
        st.error("L'ultimo accesso non può essere prima dell'iscrizione.")
    else:
        gruppo= trova_gruppo (accessi, importo, giorni_ultimo_accesso)

        #se viene premuto il pulsante aggiungi viene aggiunto il cliente nuovo alla lista
        if pulsante_aggiungi:
            totale_clienti= len(tabella_clienti) +1 
            codice_cliente="CC" + str(totale_clienti).zfill(4)
            nuovo_cliente= {
                "ID_cliente": codice_cliente,
                "Zona": zona_nuovo,
                "Data_iscrizione": pd.Timestamp(data_iscrizione),
                "Piano": piano,
                "Accessi_90gg": accessi,
                "Giorni_ultimo_accesso": giorni_ultimo_accesso,
                "Categoria_preferita": categoria_nuovo,
                "Importo_totale_90gg": importo,
                "Profilo_simulato": "Nuovo", #per indicare che non e' uno dei clienti simulati di base, ma e' stato aggiunto
                "Nome_gruppo": gruppo,
            }
            st.session_state["clienti_aggiunti"].append(nuovo_cliente)
            st.session_state["messaggio"] = f"Cliente aggiunto al gruppo {gruppo}. I clienti sono ora {totale_clienti}."
            st.rerun()  #riavvia lo script da capo, così si aggiorna tutto con ilnuovo cliente

        #stampo a video il gruppo del cliente e l'offerta da proporgli
        st.success(f"Gruppo: **{gruppo}**. Importo negli ultimi 90 giorni: {importo}€.")
        st.write(f"**Offerta:** {OFFERTE[gruppo]}")

#elimina i clienti aggiunti per tornare ai 450 clienti originali
if len(st.session_state["clienti_aggiunti"]) >0 and st.button("Elimina i clienti aggiunti"):
    st.session_state["clienti_aggiunti"] = []
    st.rerun()