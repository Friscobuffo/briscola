from random import randint
from random import random
from time import time, sleep
import pickle
import os

def puntiCarta(carta):
    valore = carta%10 + 1
    if valore == 1: return 11
    if valore == 3: return 10
    if valore < 8: return 0
    return valore - 6

def haPresoIlPrimo(briscola, cartaTirataPerPrima, cartaTirataPerSeconda):
    seme0 = int(cartaTirataPerPrima/10)
    seme1 = int(cartaTirataPerSeconda/10)
    if seme0 == seme1:
        if puntiCarta(cartaTirataPerPrima) > puntiCarta(cartaTirataPerSeconda): return True
        if puntiCarta(cartaTirataPerPrima) < puntiCarta(cartaTirataPerSeconda): return False
        return cartaTirataPerPrima > cartaTirataPerSeconda
    if seme0 == briscola: return True
    if seme1 == briscola: return False
    return True

class Mazzo():
    def __init__(self):
        self.carte = []
        for carta in range (0,40):
            self.carte.append(carta)

    def carteRimaste(self):
        return len(self.carte)

    def pesca(self):
        if self.carteRimaste() == 1:
            return self.carte.pop()
        n = randint(0, self.carteRimaste()-1)
        return self.carte.pop(n)

    def mischia(self):
        self.carte = []
        for carta in range (0,40):
            self.carte.append(carta)

class GiocatoreIA():
    def __init__(self, epsilon, decay, alpha):
        self.mano = []
        self.punti = 0
        self.ia = {}
        self.epsilon = epsilon
        self.decay = decay
        self.alpha = alpha
        self.statoPrecedente = None
        self.azionePrecedente = None
        self.rewardPrecedente = None
        self.learn = False

    def impara(self):
        self.learn = True

    def nonImparare(self):
        self.learn = False

    def reset(self):
        self.mano = []
        self.statoPrecedente = None
        self.azionePrecedente = None
        self.rewardPrecedente = None
        self.punti = 0

    def aggiungiInMano(self, carta):
        self.mano.append(carta)

    def aggiungiPunti(self, punti):
        self.punti += punti
    
    def statoCarta(self, carta):
        seme = int(carta/10)
        punti = puntiCarta(carta)
        if 0<punti<10:
            punti=1
        elif punti>=10:
            punti=2
        return (3*seme + punti,)
    
    def statoMano(self):
        statoMano = tuple()
        for carta in self.mano:
            statoMano += self.statoCarta(carta)
        return statoMano

    def scegliAzione(self, stato):
        carteInMano = len(self.mano)
        if carteInMano == 1:
            return 0
        if self.learn:
            if (random() < self.epsilon):
                azione = randint(0,carteInMano-1)
            else:
                azione = self.azioneMigliore(stato)
        else:
            azione = self.azioneMigliore(stato)
        return azione
    
    def tira(self, azione):
        return self.mano.pop(azione)
    
    def aggiornaValoreStato(self, nuovaAzione, nuovoStato, nuovoReward, partitaFinita):
        if self.statoPrecedente != None:
            valoreStatoPrecedente = self.valore(self.statoPrecedente, self.azionePrecedente)
            valoreMassimoNuovoStato = max([self.valore(nuovoStato, a) for a in range(3)])
            valoreStatoPrecedente += self.alpha*(self.rewardPrecedente + self.decay*valoreMassimoNuovoStato - valoreStatoPrecedente)
            self.ia[(self.azionePrecedente,)+self.statoPrecedente] = valoreStatoPrecedente
            if partitaFinita:
                valoreNuovoStato = self.valore(nuovoStato, nuovaAzione)
                valoreNuovoStato += self.alpha*(nuovoReward - valoreNuovoStato)
                self.ia[(nuovaAzione,)+nuovoStato] = valoreNuovoStato
        self.statoPrecedente = nuovoStato
        self.rewardPrecedente = nuovoReward
        self.azionePrecedente = nuovaAzione

    def valore(self, stato, azione):
        if self.ia.get((azione,)+stato) == None:
            return 0 # valore di default
        value = self.ia.get((azione,)+stato)
        return value

    def azioneMigliore(self, stato):
        carteInMano = len(self.mano)
        if carteInMano == 1: # non c'è nulla da scegliere
            return 0
        valoriAzioni = []
        for i in range(carteInMano):
            valoriAzioni.append(self.valore(stato,i))
        if valoriAzioni.count(0) == carteInMano:
            return randint(0,carteInMano-1)
        massimo = max(valoriAzioni)
        return valoriAzioni.index(massimo)

class GiocatoreCasuale():
    def __init__(self):
        self.mano = []
        self.punti = 0

    def reset(self):
        self.mano = []
        self.punti = 0

    def aggiungiInMano(self, carta):
        self.mano.append(carta)

    def aggiungiPunti(self, punti):
        self.punti += punti

    def scegliAzione(*_):
        return 0

    def tira(self, *_):
        return self.mano.pop(0)

    def statoCarta(self, carta):
        seme = int(carta/10)
        punti = puntiCarta(carta)
        if 0<punti<10:
            punti=1
        elif punti>=10:
            punti=2
        return (3*seme + punti,)
    
    def statoMano(self):
        statoMano = tuple()
        for carta in self.mano:
            statoMano += self.statoCarta(carta)
        return statoMano

class Environment():
    def __init__(self, epsilon, decay, alpha):
        path = os.getcwd()
        if os.path.exists(path+"/ia0.pk1"):
            if os.path.exists(path+"/ia1.pk1"):
                if os.path.exists(path+"/infos.pk1"):
                    self.importaDaFile()
        else:
            self.giocatore0 = GiocatoreIA(epsilon, decay, alpha)
            self.giocatore1 = GiocatoreIA(epsilon, decay, alpha)
            self.epsilon = epsilon
            self.decay = decay
            self.alpha = alpha
            self.tempoTotaleAddestramento = 0
            self.totalePartiteGiocateAddestramento = 0
        self.mazzo = Mazzo()
        self.giocatoreCasuale = GiocatoreCasuale()

    def reset(self, controGiocatoreCasuale):
        if controGiocatoreCasuale:
            self.giocatore0.nonImparare()
            self.giocatore1.nonImparare()
        else:
            self.giocatore0.impara()
            self.giocatore1.impara()
        self.mazzo.mischia()
        self.giocatore0.reset()
        self.giocatore1.reset()
        self.giocatoreCasuale.reset()
        self.cartaInFondo = self.mazzo.pesca()
        self.briscoleUscite = 0
        # infos stato generico partita per l'ia
        self.briscola = int(self.cartaInFondo/10)
        self.puntiCartaInFondoAlmeno10 = (puntiCarta(self.cartaInFondo) >= 10)
        self.uscitoAlmenoUnCaricoPerOgniSeme = [False, False, False, False]
        self.fasciaBriscoleUscite = 0
        # scelta di chi inizia
        turnoDelGiocatore0 = randint(0,1)
        if controGiocatoreCasuale:
            if turnoDelGiocatore0 == 0:
                self.giocatoreTiraPerPrimo = self.giocatore0
                self.giocatoreTiraPerSecondo = self.giocatoreCasuale
            else:
                self.giocatoreTiraPerPrimo = self.giocatoreCasuale
                self.giocatoreTiraPerSecondo = self.giocatore0
        else:
            if turnoDelGiocatore0 == 0:
                self.giocatoreTiraPerPrimo = self.giocatore0
                self.giocatoreTiraPerSecondo = self.giocatore1
            else:
                self.giocatoreTiraPerPrimo = self.giocatore1
                self.giocatoreTiraPerSecondo = self.giocatore0
        for _ in range(3):
            self.fasePescata()

    def step(self, controGiocatoreCasuale):
        puntiPrimoGiocatoreAlmeno45 = self.giocatoreTiraPerPrimo.punti > 45
        puntiSecondoGiocatoreAlmeno45 = self.giocatoreTiraPerSecondo.punti > 45
        statoPerPrimoGiocatore = self.giocatoreTiraPerPrimo.statoMano() + (puntiSecondoGiocatoreAlmeno45, self.puntiCartaInFondoAlmeno10,
                        self.briscola, self.fasciaBriscoleUscite) + tuple(self.uscitoAlmenoUnCaricoPerOgniSeme)
        
        azionePrimoGiocatore = self.giocatoreTiraPerPrimo.scegliAzione(statoPerPrimoGiocatore)
        cartaTirataPerPrima = self.giocatoreTiraPerPrimo.tira(azionePrimoGiocatore)

        statoCartaTirataPerPrima = self.giocatore0.statoCarta(cartaTirataPerPrima)
        statoPerSecondoGiocatore = self.giocatoreTiraPerSecondo.statoMano() + (puntiPrimoGiocatoreAlmeno45, self.puntiCartaInFondoAlmeno10,
                        self.briscola, self.fasciaBriscoleUscite) + tuple(self.uscitoAlmenoUnCaricoPerOgniSeme) + statoCartaTirataPerPrima
        
        azioneSecondoGiocatore = self.giocatoreTiraPerSecondo.scegliAzione(statoPerSecondoGiocatore)
        cartaTirataPerSeconda = self.giocatoreTiraPerSecondo.tira(azioneSecondoGiocatore)
        # aggiornamento stato generico
        if puntiCarta(cartaTirataPerPrima) >= 10:
            semeCarta = int(cartaTirataPerPrima/10)
            self.uscitoAlmenoUnCaricoPerOgniSeme[semeCarta] = True
        if puntiCarta(cartaTirataPerSeconda) >= 10:
            semeCarta = int(cartaTirataPerSeconda/10)
            self.uscitoAlmenoUnCaricoPerOgniSeme[semeCarta] = True
        if int(cartaTirataPerPrima/10) == self.briscola:
            self.briscoleUscite += 1
            if self.briscoleUscite >= 7:
                self.fasciaBriscoleUscite = self.briscoleUscite
        if int(cartaTirataPerSeconda/10) == self.briscola:
            self.briscoleUscite += 1
            if self.briscoleUscite >= 7:
                self.fasciaBriscoleUscite = self.briscoleUscite
        if self.mazzo.carteRimaste() >= 1:
            self.fasePescata()
        punti = puntiCarta(cartaTirataPerPrima) + puntiCarta(cartaTirataPerSeconda)
        reward = punti
        if haPresoIlPrimo(self.briscola, cartaTirataPerPrima, cartaTirataPerSeconda):
            self.giocatoreTiraPerPrimo.aggiungiPunti(punti)
            partitaFinita = self.partitaFinita()
            if partitaFinita: reward += 120
            if not controGiocatoreCasuale:
                self.giocatoreTiraPerPrimo.aggiornaValoreStato(azionePrimoGiocatore, statoPerPrimoGiocatore, reward, partitaFinita)
                self.giocatoreTiraPerSecondo.aggiornaValoreStato(azioneSecondoGiocatore, statoPerSecondoGiocatore, -reward, partitaFinita)
        else:
            self.giocatoreTiraPerSecondo.aggiungiPunti(punti)
            partitaFinita = self.partitaFinita()
            if partitaFinita: reward += 120
            if not controGiocatoreCasuale:
                self.giocatoreTiraPerPrimo.aggiornaValoreStato(azionePrimoGiocatore, statoPerPrimoGiocatore, -reward, partitaFinita)
                self.giocatoreTiraPerSecondo.aggiornaValoreStato(azioneSecondoGiocatore, statoPerSecondoGiocatore, reward, partitaFinita)
            self.giocatoreTiraPerPrimo, self.giocatoreTiraPerSecondo = self.giocatoreTiraPerSecondo, self.giocatoreTiraPerPrimo

        return partitaFinita

    def fasePescata(self):
        if self.mazzo.carteRimaste() > 1:
            pescata = self.mazzo.pesca()
            self.giocatoreTiraPerPrimo.aggiungiInMano(pescata)
            pescata = self.mazzo.pesca()
            self.giocatoreTiraPerSecondo.aggiungiInMano(pescata)
        else:
            pescata = self.mazzo.pesca()
            self.giocatoreTiraPerPrimo.aggiungiInMano(pescata)
            self.giocatoreTiraPerSecondo.aggiungiInMano(self.cartaInFondo)

    def partitaFinita(self):
        return (self.giocatoreTiraPerPrimo.punti>60 or
                self.giocatoreTiraPerSecondo.punti>60 or
                (self.giocatoreTiraPerPrimo.punti==60 and self.giocatoreTiraPerSecondo.punti==60))

    def addestraIA(self, numeroEpisodi):
        print("Addestramento IA con", numeroEpisodi, "episodi")
        self.simulaPartite(numeroEpisodi, controGiocatoreCasuale=False)

    def simulaPartite(self, numeroEpisodi, controGiocatoreCasuale):
        vinteDalGiocatore0 = 0
        pareggiateDalGiocatore0 = 0
        addestra = not controGiocatoreCasuale
        if addestra:
            timestampInizio = time()
        for i in range(numeroEpisodi):
            self.reset(controGiocatoreCasuale)
            finitaPartita = False
            while not finitaPartita:
                finitaPartita = self.step(controGiocatoreCasuale)
            if addestra:
                self.totalePartiteGiocateAddestramento += 1
            if self.giocatore0.punti > 60:
                vinteDalGiocatore0 += 1
            elif self.giocatore0.punti == 60:
                pareggiateDalGiocatore0 += 1
            percent = "{:.2f}".format((i*100)/numeroEpisodi)
            print(f'\r{percent}%', end = '')
        if addestra:
            tempoAddestramento = time() - timestampInizio
            self.tempoTotaleAddestramento += tempoAddestramento
        if controGiocatoreCasuale:
            print("\r - Percentuale vittoria:   [", 100*vinteDalGiocatore0/numeroEpisodi,"%]", sep="")
            print(" - Percentuale pareggio:   [", 100*pareggiateDalGiocatore0/numeroEpisodi, "%]", sep="")
            sconfitteDelGiocatore0 = numeroEpisodi - vinteDalGiocatore0 - pareggiateDalGiocatore0
            print(" - Percentuale sconfitta:  [", 100*sconfitteDelGiocatore0/numeroEpisodi, "%]", sep="")
            print()

    def printInfosAddestramento(self):
        secondi = int(self.tempoTotaleAddestramento)
        minuti = int(secondi/60)
        secondi = secondi%60
        ore = int(minuti/60)
        minuti = minuti%60
        print("Tempo totale addestramento ia: ", ore, "h ", minuti, "m ", secondi, "s", sep="")
        totaleStatiEsplorati = len(self.giocatore0.ia)
        print("Totale stati esplorati:", totaleStatiEsplorati)
        print("Totale partite addestramento ia:", self.totalePartiteGiocateAddestramento)
        print()
        print("Epsilon:", self.epsilon)
        print("Alpha:", self.alpha)
        print("Decay:", self.decay)
        print()
        path = os.getcwd()
        if os.path.exists(path+"/ia0.pk1"):
            if os.path.exists(path+"/ia1.pk1"):
                if os.path.exists(path+"/infos.pk1"):
                    dimensioneIA0 = round((os.stat(path+"/ia0.pk1").st_size)/(1000*1000), 1)
                    dimensioneIA1 = round((os.stat(path+"/ia1.pk1").st_size)/(1000*1000), 1)
                    print("Dimensione ia0:", dimensioneIA0, "MB")
                    print("Dimensione ia1:", dimensioneIA1, "MB")
                    print()

    def simulaControGiocatoreCasuale(self, numeroPartite=10_000):
        print("Simulazione contro giocatore che fa mosse casuali")
        self.simulaPartite(numeroPartite, controGiocatoreCasuale=True)

    def salvaIaSuFile(self):
        with open("ia0.pk1", "wb") as fp:
            pickle.dump(self.giocatore0.ia, fp)
            fp.close()
        with open("ia1.pk1", "wb") as fp:
            pickle.dump(self.giocatore1.ia, fp)
            fp.close()
        with open("infos.pk1", "wb") as fp:
            infos = {"tempoTotaleAddestramento": self.tempoTotaleAddestramento,
                     "totalePartiteGiocateAddestramento": self.totalePartiteGiocateAddestramento,
                     "epsilon": self.epsilon,
                     "decay": self.decay,
                     "alpha": self.alpha}
            pickle.dump(infos, fp)
            fp.close()
        print("Finito di salvare")
        dir = os.getcwd()
        dimensioneIA0 = int((os.stat(dir+"/ia0.pk1").st_size)/(1024*1024))
        dimensioneIA1 = int((os.stat(dir+"/ia1.pk1").st_size)/(1024*1024))
        print("Dimensione ia0:", dimensioneIA0, "MB")
        print("Dimensione ia1:", dimensioneIA1, "MB")

    def importaDaFile(self):
        with open('ia0.pk1', 'rb') as fp:
            ia0 = pickle.load(fp)
            fp.close()
        with open('ia1.pk1', 'rb') as fp:
            ia1 = pickle.load(fp)
            fp.close()
        with open("infos.pk1", "rb") as fp:
            infos = pickle.load(fp)
            fp.close()
        self.tempoTotaleAddestramento = infos["tempoTotaleAddestramento"]
        self.totalePartiteGiocateAddestramento = infos["totalePartiteGiocateAddestramento"]
        self.epsilon = infos["epsilon"]
        self.decay = infos["decay"]
        self.alpha = infos["alpha"]
        self.giocatore0 = GiocatoreIA(self.epsilon, self.decay, self.alpha)
        self.giocatore0.ia = ia0
        self.giocatore1 = GiocatoreIA(self.epsilon, self.decay, self.alpha)
        self.giocatore1.ia = ia1
        print("Finito di importare ia da file")

    def decrementaEpsilon(self, decrement=0.993):
        self.epsilon *= decrement
        self.giocatore0.epsilon = self.epsilon
        self.giocatore1.epsilon = self.epsilon

def addestra():
    epsilon = 0.1
    decay = 0.9
    alpha = 0.2
    oreAddestramento = 1
    env = Environment(epsilon, decay, alpha)
    inizio = time()
    while (time()-inizio) < oreAddestramento*60*60:
        env.addestraIA(numeroEpisodi=25_000) # dura circa una 10ina di secondi
        os.system("clear")
        env.printInfosAddestramento()
        env.simulaControGiocatoreCasuale()
        #env.decrementaEpsilon()
        sleep(5)
    env.salvaIaSuFile()

addestra()
