import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

#le tre variabili usate per formare i gruppi di clienti
VARIABILI = ["Accessi_90gg", "Importo_totale_90gg", "Giorni_ultimo_accesso"]
tabella_clienti = pd.read_csv("dati/clienti.csv")

#sostituzione dei valori mancanti con la mediana della colonna
for colonna in VARIABILI:
    mediana = tabella_clienti[colonna].median()
    tabella_clienti[colonna] = tabella_clienti[colonna].fillna(mediana)

#le variabili sono su scale diverse (numero di accessi, euro spesi, giorni dall'ultimo accesso)
#K-means usa le distanze, quindi le porto sulla stessa scala e si vede quanto ogni valore è sopra o sotto la media
dati_standardizzati = StandardScaler().fit_transform(tabella_clienti[VARIABILI])

#prova di K da 3 a 5
silhouette_migliore = -1 #parto dal valore più basso possibile per trovare il valore più alto
for k in range(3, 6): 
    modello_kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
    gruppo_assegnato = modello_kmeans.fit_predict(dati_standardizzati)
    indice_silhouette = silhouette_score(dati_standardizzati, gruppo_assegnato) #calcola separazione gruppi con numero tra -1 e +1
    print("k =", k, " inertia =", round(modello_kmeans.inertia_, 1), " silhouette =", round(indice_silhouette, 3))
    if indice_silhouette > silhouette_migliore:
        silhouette_migliore = indice_silhouette
        k_migliore = k
        tabella_clienti["Gruppo"] = gruppo_assegnato
print("k scelto:", k_migliore)


#assegno un nome a ogni gruppo, in base alle medie
medie_gruppi = tabella_clienti.groupby("Gruppo")[VARIABILI].mean()

#Gli inattivi sono il gruppo che non entra da più giorni
nomi_gruppi = {}
gruppo_inattivi = medie_gruppi["Giorni_ultimo_accesso"].idxmax()
nomi_gruppi[gruppo_inattivi] = "Inattivi"

#Le famiglie sono il gruppo che spende di piu, poi divise tra le più attive e le meno attive
altri_gruppi = medie_gruppi.drop(gruppo_inattivi)
famiglie = altri_gruppi.sort_values("Importo_totale_90gg", ascending=False).head(2)
altri_gruppi = altri_gruppi.drop(famiglie.index)
famiglie = famiglie.sort_values("Accessi_90gg", ascending=False)
nomi_gruppi[famiglie.index[0]] = "Famiglie attive"
nomi_gruppi[famiglie.index[1]] = "Famiglie meno attive"

#con gli ultimi 2 gruppi rimasti, si vedono i più attivi e quelli meno attivi tra quelli che hanno tanti accessi
altri_gruppi = altri_gruppi.sort_values("Accessi_90gg", ascending=False)
nomi_gruppi[altri_gruppi.index[0]] = "Attivi con piano base"
nomi_gruppi[altri_gruppi.index[1]] = "Intermedi e nuovi"


tabella_clienti["Nome_gruppo"] = tabella_clienti["Gruppo"].map(nomi_gruppi)

#tabella riassuntiva che stampa nel prompt la divisione dei gruppi quando si esegue lo script di segmentazione
profilo_gruppi = tabella_clienti.groupby("Nome_gruppo")[VARIABILI].mean().round(1)
profilo_gruppi["Clienti"] = tabella_clienti["Nome_gruppo"].value_counts()
print(profilo_gruppi.to_string()) #stampa la tabella intera senza tagliare le colonne nel prompt

tabella_clienti.to_csv("dati/clienti_segmentati.csv", index=False)
        
        
