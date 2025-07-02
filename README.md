# messaggi_in_bottiglia

0.1) operazione fondamentale:
    dato un testo, scomporlo in un vettore di parole
    - portare tutte le parole in minuscolo
    - eliminare le stopword
    --- convertire il plurale in singolare
    --- convertire il femminile in maschile
    --- sostituire i termini con dei sinonimi di uso piu' frequente
    --- convertire i verbi all'infinito
    - applicare uno stemmer
    ottenendo cosi' una documento rappresentato da una list-of-words 'doc'

0.2) potrebbe aver senso scmporre il documento in una lista di liste di
    parole, dove la lista di parole rappresenta un paragrafo.
    I paragrafi sono identificati dai segni di interpunzione ('.', '?', '!',
    '(...)', '-...-', ecc) tenendo conto delle eccezioni (ad esempio "H.G. Wells"
    oppure "H. G. Wells", "S.p.A.", ...)
    
1) dato i doc, creare il dizionario
2) dato il dizionario, convertire il doc in un 'bow'

Una lista di bow e' un 'corpus'

Un corpus puo' essere semplificato usando uno dei 'Topic Modelling': bisogna
indicare quanti topic e quante parole in ogni topic (le stesse per tutti i topic)

PROBLEMA: 
    1) come capire quanti topic creare?
    2) come assegnare una 'categoria' ai topic?
       Potrebbe non avere senso, se si sa gia' che certi topic appartengono 
       ad una determinata categoria:
       ad esempio, se un certa parola appartiene a piu' categorie, il topic
       appartiene alla categoria prevalente tra tutte le categorie associate
       a tutte le parole che compongono il topic.
       In ogni caso, si possono assegnare dei pesi per l'appartenenza di un topic
       ad una categoria.

3) create il topic-model ('tm') passandogli il corpus.
   A questo punto il tm e' una trasformazione tra il vector-space originale (il
   corpus) ed il nuovo vector-space
   
NOTA: una volta creato il dizionario, non e' piu' necessario filtrare il testo da
      trattare, perche' se una parola non e' presente nel dizionario, automaticamente
      viene esclusa nella conversione da sequenza di parole a 'bow'


https://en.wikipedia.org/wiki/Cosine_similarity
https://en.wikipedia.org/wiki/Kullback%E2%80%93Leibler_divergence#Symmetrised_divergence
