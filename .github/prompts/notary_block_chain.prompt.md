---
agent: agent
---
You are a senior system architect, python developer, crypto specialist.

The project is a blockchain used to authorize notary documents. Documentation below:

\documentclass[12pt, a4paper]{article}

\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[polish]{babel}
\usepackage{graphicx}      
\usepackage{geometry}      
\usepackage{hyperref}      
\usepackage{float}         
\usepackage{listings}   

\usepackage{tabularx}
\usepackage{booktabs}
\usepackage{makecell}

\geometry{
 a4paper,
 total={170mm,257mm},
 left=20mm,
 top=20mm,
}

\title{\textbf{Dokumentacja Techniczna Systemu Notarialnego}\\Moduł Rdzenia Blockchain}
\author{Autorzy }
\date{Grudzień 2025}

\begin{document}

\maketitle
\tableofcontents
\newpage

\section{Wstęp}
Projekt przedstawia system informatyczny oparty na prywatnej sieci blockchain, służący do bezpiecznego rejestrowania czynności notarialnych, takich jak zmiany udziałów w spółkach czy wyniki głosowań. Rozwiązanie wykorzystuje mechanizm autoryzacji (Proof of Authority), w którym tylko zweryfikowane węzły mają prawo zatwierdzać nowe dane, co eliminuje anonimowość i zwiększa zaufanie do sieci. Aplikacja automatycznie weryfikuje poprawność transakcji zgodnie z regułami biznesowymi, a zastosowana kryptografia gwarantuje, że historii wpisów nie da się sfałszować ani usunąć. Całość działa jako rozproszona baza danych, umożliwiająca notariuszom bezpieczną i bezpośrednią wymianę informacji bez konieczności polegania na jednym centralnym serwerze. 

\begin{figure}[h!]
    \centering
    \includegraphics[width=0.75\linewidth]{peer2peer_deployment.png}
    \caption{Diagram Wdrożenia sieci Peer To Peer}
    \label{fig:placeholder}
\end{figure}

\section{Moduł 1: Blockchain Core}

\subsection{Opis Ogólny}
Moduł Blockchain Core stanowi fundament całego systemu. Jest to komponent odseparowany od logiki biznesowej, którego jedynym celem jest zapewnienie ciągłości oraz bezpieczeństwa łańcucha bloków.

W tym module stosujemy mechanizm Proof of Authority, w którym prawo do zatwierdzania nowych bloków posiadają wyłącznie autoryzowane węzły, identyfikowane za pomoca kluczy kryptograficznych. 

\subsection{Kluczowe Odpowiedzialności}
Moduł realizuje następujące zadania:
\begin{itemize}
    \item \textbf{Definicja Struktury Danych:} Zarządzanie klasą \texttt{Block} oraz strukturą łańcucha, gwarantując ciagłość poprzez powiązanie hashem poprzedniego bloku (\texttt{parentHash}).
    \item \textbf{Implementacja Proof of Authority:} Weryfikacja tożsamości autora bloku poprzez pole \texttt{miner} oraz walidacja podpisu cyfrowego zawartego w polu \texttt{extraData}.
    \item \textbf{Gwarancja Integralności:} Obliczanie skrótów kryptograficznych dla transakcji (\texttt{transactionsRoot}) oraz stanu systemu (\texttt{stateRoot}), co zabezpiecza bazę danych przed nieautoryzowaną modyfikacją.
    \item \textbf{Zarządzanie Czasem:} Synchronizacja bloków zgodnie ze znacznikiem czasu (\texttt{timestamp}).
\end{itemize}

\subsection{Wzorce Projektowe}
W architekturze modułu zastosowano wzorzec Builder, który wykorzystujemy w klasie \texttt{BlockBuilder} do konstruowania obiektów bloków. Dlaczego użyliśmy tego wzorca:

\begin{itemize}
    \item \textbf{Czytelny Interfejs:} Obiekt bloku w architekturze Proof of Authority posiada wiele pól konfiguracyjnych (np. parentHash, miner, timestamp, stateRoot, extraData). Użycie tradycyjnego konstruktora z dużą liczbą parametrów tego samego typu (głównie String) byłoby nieczytelne i podatne na błędy. Builder zapewnia czytelny interfejs.
    
    \item \textbf{Gwarancja Niemodyfikowalności:} Podstawową cechą systemu blockchain jest to, że raz utworzony i podpisany blok nie może być edytowany. Klasa \texttt{Block} nie posiada publicznych setterów. Wzorzec Builder pozwala zebrać wszystkie zmienne dane, a następnie wywołać metodę \texttt{build()}, która zwraca gotowy, "zapieczętowany" obiekt.
    
    \item \textbf{Weryfikacja Danych:} Builder przejmuje odpowiedzialność za weryfikację spójności danych przed utworzeniem obiektu. W metodzie \texttt{build()} następuje sprawdzenie parametrów oraz wyliczenie skrótów kryptograficznych dla zawartych transakcji.
\end{itemize}


\subsection{Diagram Klas}
% MIEJSCE NA TWÓJ DIAGRAM KLAS
\begin{figure}[H]
    \centering
    \includegraphics[width=0.9\textwidth]{diagram_klas_blockchain_v2.png}
    \caption{Diagram klas modułu Blockchain Core}
    \label{fig:class_diagram}
\end{figure}

\subsection{Proces Tworzenia i Walidacji Bloku}
W procesie dodawania nowego bloku korzystamy z procesu autoryzacji:
\begin{enumerate}
    \item \textbf{Inicjalizacja:} Serwis Notariusza tworzy instancję \texttt{BlockBuilder}.
    \item \textbf{Agregacja:} Do buildera dodawane są \texttt{DokumentyNotarialne}.
    \item \textbf{Budowanie:} Obiekt pobiera hash ostatniego bloku (\texttt{parentHash}) dla zachowania ciągłości.
    \item \textbf{Podpisanie:} Wykonywana jest metoda \texttt{signBlock}. System generuje podpis cyfrowy przy użyciu klucza prywatnego Notariusza i zapisuje go w \texttt{extraData}.
    \item \textbf{Weryfikacja:} Pozostałe węzły w sieci sprawdzają, czy adres w polu \texttt{miner} jest uprawniony do tworzenia bloków i czy podpis jest poprawny.
\end{enumerate}

\subsection{Diagram Sekwencji}
\begin{figure}[H]
    \centering
    \includegraphics[width=0.9\textwidth]{sekwencji_v2.png}
    \caption{Diagram sekwencji procesu tworzenia i podpisywania bloku.}
    \label{fig:sequence_diagram}
\end{figure}
\newpage
\section{Moduł 2: Business Logic}

\subsection{Opis Ogólny}
Moduł Logiki Biznesowej jest warstwą aplikacyjną, która nadaje sens danym przechowywanym w łańcuchu bloków. Podczas gdy \textit{Blockchain Core} dba o to, czy blok jest poprawny kryptograficznie, ten moduł odpowiada na pytanie: "czy transakcja jest poprawna prawnie i biznesowo".

W module tym zaimplementowano mechanizm, który automatyzuje weryfikację reguł notarialnych (np. sprzedaż udziałów, głosowanie nad uchwałami) przed ich trwałym zapisaniem w rejestrze.

\subsection{Kluczowe Odpowiedzialności}
Moduł realizuje następujące zadania:
\begin{itemize}
    \item \textbf{Abstrakcja Dokumentów Notarialnych:} Definicja wspólnego interfejsu dla różnych typów operacji (przelew udziałów, uchwała, dywidenda), co pozwala na ich jednolite traktowanie przez mechanizmy blokowe.
    \item \textbf{Walidacja Biznesow:} Weryfikacja warunków koniecznych do zawarcia transakcji, w szczególności:
    \begin{itemize}
        \item Sprawdzenie pokrycia (czy zbywca posiada wystarczającą liczbę udziałów).
        \item Weryfikacja uprawnień (czy strona transakcji jest autoryzowanym podmiotem).
    \end{itemize}
    \item \textbf{Zarządzanie Stanem Świata (World State):} Przetwarzanie historii transakcji w celu obliczenia aktualnego stanu posiadania dla każdego udziałowca.
    \item \textbf{Serializacja Danych:} Konwersja obiektów biznesowych do formatu JSON, wymaganego przez strukturę bloku.
\end{itemize}


\subsection{Wzorce Projektowe}
Architektura modułu opiera się na wzorcu \textbf{Metoda Wytwórcza (Factory Method)}. Zastosowanie tego wzorca kreacyjnego pozwala na odseparowanie procesu inicjalizacji dokumentów od logiki ich walidacji biznesowej.

\begin{itemize}
    \item \textbf{Struktura:} Klasa abstrakcyjna \texttt{DocumentProvider} definiuje interfejs metody wytwórczej, natomiast jej konkretyzacja następuje w klasach \texttt{FinancialActionProvider} (obsługa operacji kapitałowych) oraz \texttt{GovernanceActionProvider} (obsługa decyzji zarządczych).
    \item \textbf{Izolacja i Skalowalność:} Wzorzec umożliwia rozszerzanie systemu o nowe typy czynności notarialnych bez ingerencji w kod odpowiedzialny za utrzymanie spójności blockchaina. Realizuje to zasadę Open/Closed poprzez polimorficzne tworzenie obiektów implementujących wspólny interfejs \texttt{DokumentNotarialny}.
    \item \textbf{Zasada Pojedynczej Odpowiedzialności (SRP):} Logika decyzyjna dotycząca tego, który dokument powołać do życia na podstawie danych wejściowych, jest oddelegowana do wyspecjalizowanych dostawców, co eliminuje konieczność stosowania centralnych struktur kontrolnych typu \textit{switch-case}.
\end{itemize}

\subsection{Diagram Klas}
Diagram przedstawia strukturę modułu Business Logic z uwzględnieniem podziału na abstrakcyjnych twórców oraz konkretne produkty. Relacja agregacji z klasą \texttt{Block} wskazuje na sposób przechowywania wygenerowanych i zwalidowanych dokumentów w strukturze księgi.

\begin{figure}[h]
    \centering
    \includegraphics[width=1.0\textwidth]{diagram_klas_business_logic.png}
    \caption{Diagram klas modułu Business Logic z zastosowaniem wzorca Factory Method.}
\end{figure}
\subsection{Logika walidacji biznesowej}
Poniższy diagram sekwencji przedstawia logikę działania walidacji biznesowej w przypadku transakcji zbycia udziałów. System w sposób zautomatyzowany wykonuje sekwencję sprawdzeń (walidacja stanu konta, walidacja posiadanych akcji) przed zatwierdzeniem operacji. Jest to mechanizm zapobiegający błędom i oszustwom (np. \textit{double spending}) na poziomie logiki biznesowej, zanim transakcja trafi do bloku.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.9\textwidth]{diagram_sekwencji_transferu_udziałów.png}
    \caption{Diagram sekwencji procesu walidacji transakcji (Smart Contract execution)}
    \label{fig:sequence_diagram_smart_contract}
\end{figure}

\section{Moduł 3: Network \& Discovery}

\subsection{Opis Ogólny}
Moduł sieciowy odpowiada za komunikację między węzłami w sieci lokalnej (LAN). Jego głównym zadaniem jest utrzymanie spójności rozproszonego rejestru poprzez wymianę bloków i transakcji.

\subsection{Kluczowe Funkcjonalności}
Moduł realizuje następujące zadania:
\begin{itemize}
    \item \textbf{Autonomiczne Odkrywanie:} Automatyczne znajdowanie innych węzłów w sieci lokalnej przez broadcast UDP.
    \item \textbf{Zarządzanie Połączeniami (TCP):} Utrzymywanie stałych połączeń z losowo wybranymi partnerami (max 3 peerów).
    \item \textbf{Protokół Handshake:} Weryfikacja tożsamości węzła oraz wymiana metadanych przed rozpoczęciem właściwej transmisji danych.
    \item \textbf{Synchronizacja Bloków:} Mechanizm dociągania brakującej historii łańcucha od partnera posiadającego najdłuższą wersję.
\end{itemize}

\subsection{Architektura Komponentów}
Struktura modułu opiera się na centralnym punkcie wejścia (Fasada) oraz wyspecjalizowanych menedżerach.

\subsubsection{1. NetworkManager - główny entry point}
Główna klasa modułu. Inicjalizuje podsystemy.
\begin{itemize}
    \item Udostępnia proste metody publiczne: \texttt{start()}, \texttt{broadcast\_tx()}, \texttt{broadcast\_block()}.
    \item Komunikuje ze sobą \texttt{DiscoveryService} i \texttt{PeerManager}.
\end{itemize}

\subsubsection{PeerManager i PeerConnection}
Odpowiada za warstwę transportową opartą na TCP.
\begin{itemize}
    \item \textbf{PeerManager:} Implementuje interfejs \texttt{IConnectionListener}. Zarządza połączeniami, decyduje o rozgłaszaniu wiadomości oraz wybiera "najlepszego peera" do synchronizacji.
    \item \textbf{PeerConnection:} Reprezentuje pojedyncze połączenie. Posiada wewnętrzną maszynę stanów (CONNECTING $\to$ HANDSHAKE $\to$ READY). Przechowuje metadane partnera: \texttt{remote\_height} (wysokość łańcucha sąsiada) oraz \texttt{remote\_hash}.
\end{itemize}

\subsubsection{BlockSynchronizer}
Komponent dedykowany do obsługi procesu synchronizacji łańcucha. Szczególnie w etapia dołączenia do sieci.
\begin{itemize}
    \item Uzyskuje stan łańcucha poprzez \texttt{IBlockchainInterface}.
    \item Gdy wykryje, że sąsiad ma wyższy blok (\texttt{remote\_height > local\_height}), inicjuje proces pobierania brakujących bloków używając komunikatów \texttt{GET\_BLOCKS}.
\end{itemize}

\subsubsection{DiscoveryService}
Implementuje mechanizm Broadcast w sieci lokalnej.
\begin{itemize}
    \item Cyklicznie wysyła pakiety UDP na adres broadcastowy.
    \item Nasłuchuje pakietów od innych węzłów i buduje kolejkę potencjalnych kandydatów do połączenia TCP.
\end{itemize}

\subsection{Bezpieczeństwo i Integracja}
W celu zachowania czystości architektury, wszelkie operacje kryptograficzne zostały wydzielone do obiektu \texttt{SecurityContext}.
\begin{itemize}
    \item Obiekt ten jest przekazywany w dół hierarchii (do każdej instancji \texttt{PeerConnection}).
    \item Zawiera \texttt{IdentityManager} (klucze własne) oraz \texttt{CertificateValidator} (zaufane certyfikaty CA Izby Notarialnej), co pozwala każdemu połączeniu na niezależną autoryzację rozmówcy.
\end{itemize}

\begin{figure}[h!]
    \centering
    \includegraphics[width=0.95\linewidth]{network3.png}
    \caption{Diagram klas modułu Network \& Discovery.}
    \label{fig:network_class_v3}
\end{figure}

\subsection{Protokół Komunikacyjny}
Komunikacja odbywa się za pomocą serializowanych obiektów JSON. Zdefiniowano następujące typy wiadomości (Enum \texttt{MessageType}):
\begin{enumerate}
    \item \textbf{HANDSHAKE:} Wymiana wersji protokołu, identyfikatora węzła oraz aktualnej wysokości łańcucha.
    \item \textbf{TRANSACTION / BLOCK:} Propagacja nowych zdarzeń w sieci.
    \item \textbf{GET\_BLOCKS / BLOCKS\_RESPONSE:} Para wiadomości służąca do mechanizmu synchronizacji historii (Request/Response).
\end{enumerate}



\newpage
\section{Moduł 4: Identity \& Security}

\subsection{Opis Ogólny}
W przeciwieństwie do publicznych łańcuchów bloków (takich jak Bitcoin), system notarialny jest siecią typu \textit{Permissioned}. Oznacza to, że tożsamość uczestników (notariuszy) musi być znana i zweryfikowana. Moduł ten odpowiada za zarządzanie certyfikatami, podpisami cyfrowymi oraz integracją z Infrastrukturą Klucza Publicznego (PKI).

\subsection{Kluczowe Odpowiedzialności}
Moduł bezpieczeństwa realizuje następujące funkcje:
\begin{itemize}
    \item \textbf{Zarządzanie Tożsamością (PKI):} Obsługa certyfikatów X.509 wydawanych przez Izbę Notarialną. Każdy węzeł musi posiadać certyfikat podpisany przez zaufany urząd certyfikacji (CA), aby móc uczestniczyć w sieci.
    \item \textbf{KeyStore i TrustStore:} Bezpieczne przechowywanie klucza prywatnego węzła (służącego do podpisywania) oraz listy zaufanych certyfikatów innych notariuszy (służącej do weryfikacji).
    \item \textbf{Podpisywanie Bloków:} Implementacja mechanizmu Proof of Authority poprzez wstrzykiwanie podpisu cyfrowego autora do pola \texttt{extraData} bloku.
    \item \textbf{Weryfikacja Podpisów:} Sprawdzanie przy każdym przychodzącym bloku, czy został on podpisany przez uprawnionego notariusza i czy certyfikat nie wygasł lub nie został unieważniony.
\end{itemize}

\subsection{Wzorce Projektowe}
Architektura modułu bezpieczeństwa opiera się na wzorcu \textbf{Fasada (Facade)}.

\begin{itemize}
    \item \textbf{IdentityManager jako Fasada:} 
    Zarządzanie kryptografią (ładowanie kluczy prywatnych, parsowanie certyfikatów X.509, weryfikacja łańcucha zaufania) jest procesem skomplikowanym i niskopoziomowym. Klasa \texttt{IdentityManager} ukrywa tę złożoność, udostępniając komponentom wyższego poziomu (takim jak \texttt{BlockSigner}) uproszczony interfejs.
    
    \item \textbf{Separacja i Użyteczność:} 
    Dzięki fasadzie, reszta systemu nie musi bezpośrednio operować na plikach kluczy (\texttt{KeyStore}) ani zarządzać listami zaufania (\texttt{TrustStore}). Programista implementujący logikę blockchaina wywołuje jedynie proste metody biznesowe, np. \texttt{signBlock()} czy \texttt{registerPeer()}, a wszelkie szczegóły implementacyjne PKI pozostają ukryte.
\end{itemize}

\subsection{Diagram Klas}
\begin{figure}[H]
    \centering
    \includegraphics[width=1.0\textwidth]{diagram_klas_identity.png}
    \caption{Diagram klas modułu tożsamości i bezpieczeństwa}
    \label{fig:class_diagram_identity}
\end{figure}

\newpage
\section{Moduł 5: Storage \& Ledger}

\subsection{Opis Ogólny}
Moduł ten odpowiada za trwałość danych (persystencję). W architekturze systemu wyraźnie rozdzielono sposób przechowywania historii od sposobu przechowywania aktualnego stanu, co pozwala na optymalizację odczytów:

\begin{enumerate}
    \item \textbf{Ledger (Księga):} Pełna, niezmienna historia wszystkich bloków i transakcji od początku istnienia systemu. Służy do audytu i synchronizacji nowych węzłów.
    \item \textbf{World State (Stan Świata):} Aktualny stan posiadania udziałów w spółkach. Gdy użytkownik pyta "ile mam udziałów?", system nie przeszukuje całej historii bloków, lecz odpytuje ten zoptymalizowany zbiór danych.
\end{enumerate}

\subsection{Kluczowe Odpowiedzialności}
Moduł realizuje następujące zadania:
\begin{itemize}
    \item \textbf{Serializacja Deterministyczna:} Konwersja obiektów bloków do formatu JSON przy użyciu dedykowanego \texttt{JsonSerializer}. Jest to krytyczne, aby hash bloku był identyczny na każdej maszynie, niezależnie od platformy systemowej.
    
    \item \textbf{Persystencja Plikowa (JSON):} 
    Ze względu na prototypowy charakter systemu oraz potrzebę łatwego audytu danych, zrezygnowano ze złożonych baz danych (typu LevelDB) na rzecz zapisu do plików tekstowych.
    \begin{itemize}
        \item \textbf{Bloki:} Każdy blok jest serializowany i dopisywany do pliku \texttt{ledger.json} (lub przechowywany jako osobny plik).
        \item \textbf{Stan:} Aktualny stan świata jest zrzucany do pliku \texttt{world\_state.json}, co pozwala na szybkie odtworzenie stanu po restarcie węzła.
    \end{itemize}

    \item \textbf{Abstrakcja Dostępu do Danych:} 
    Ukrycie fizycznej warstwy zapisu (pliki systemowe) za interfejsami repozytoriów (\texttt{BlockRepository}, \texttt{WorldStateRepository}). Pozwala to na ewentualną przyszłą migrację do bazy SQL/NoSQL bez zmian w logice biznesowej.

    \item \textbf{Spójność (Rollback):} 
    W przypadku wykrycia, że łańcuch jest niepoprawny (np. wystąpił fork lub błąd walidacji), moduł posiada mechanizmy pozwalające cofnąć zmiany w pliku stanu świata (\textit{World State}) do wersji sprzed wadliwego bloku.
\end{itemize}

\subsection{Diagram Klas}
\begin{figure}[H]
    \centering
    \includegraphics[width=1.0\textwidth]{diagram_klas_storage.png}
    \caption{Diagram klas modułu przechowywania danych}
    \label{fig:class_diagram_storage}
\end{figure}

\subsection{Proces Aktualizacji Stanu}
Poniższy diagram przedstawia kluczowy moment, w którym nowy blok zostaje zaakceptowany przez sieć, a system musi zaktualizować lokalną bazę danych (\textit{World State}).

\begin{figure}[H]
    \centering
    % Placeholder na obrazek - wklej tutaj wygenerowany diagram
    \includegraphics[width=0.9\textwidth]{sekwencja_storage_update.png}
    \caption{Diagram sekwencji aktualizacji World State po otrzymaniu bloku}
    \label{fig:sequence_storage}
\end{figure}



% \section{Komunikacja między modułami}

% W celu zapewnienia separacji odpowiedzialności między komponentami systemu, bezpośrednie wywołania metod zostały zastąpione modelem asynchronicznym. Koordynacja działań między modułami (w szczególności \texttt{Core} $\leftrightarrow$ \texttt{P2P}) odbywa się za pośrednictwem \textbf{Szyny Zdarzeń} (Event Bus), realizującej wzorzec \textit{Publish-Subscribe}.

% Wszelkie informacje przepływające w systemie są kapsułkowane w predefiniowane obiekty zdarzeń o ścisłym typowaniu. Poniższy rejestr (Tabela \ref{tab:event_registry}) definiuje standard wymiany danych.

% \begin{table}[H]
% \centering
% \renewcommand{\arraystretch}{1.5} % Zwiększa odstępy między wierszami dla czytelności
% \small % Nieco mniejsza czcionka, żeby zmieścić dużo treści
% \begin{tabularx}{\textwidth}{|>{\bfseries}l|l|X|X|}
% \hline
% \textbf{Nazwa Zdarzenia} & \textbf{Przepływ (Kto $\to$ Kogo)} & \textbf{Opis i Moment Wywołania} & \textbf{Payload (Dane)} \\ \hline

% \texttt{BlockMined} & 
% \makecell[l]{Nadawca: Core \\ Odbiorca: P2P, Storage} & 
% \textbf{Opis:} Nowy blok został pomyślnie wykopany i zatwierdzony lokalnie. \newline
% \textbf{Kiedy:} Po obliczeniu poprawnego \texttt{stateRoot}. & 
% Obiekt \texttt{Block}:
% \begin{itemize}
%     \item hash (String)
%     \item height (Long)
%     \item txList (List)
% \end{itemize} \\ \hline

% \texttt{[NAZWA\_EVENTU]} & 
% \makecell[l]{Nad: [MODUŁ] \\ Odb: [MODUŁY]} & 
% \textbf{Opis:} [Co robi ten event?] \newline
% \textbf{Kiedy:} [W którym momencie kodu?] & 
% Obiekt \texttt{[NAZWA]}:
% \begin{itemize}
%     \item [pole 1]
%     \item [pole 2]
% \end{itemize} \\ \hline

% % --- Wiersz 3: Pusty szablon do kopiowania ---
% \texttt{[NAZWA\_EVENTU]} & 
% \makecell[l]{Nad: ... \\ Odb: ...} & 
% \textbf{Opis:} ... \newline
% \textbf{Kiedy:} ... & 
% ... \\ \hline

% \end{tabularx}
% \caption{Rejestr zdarzeń systemowych (Event Registry)}
% \label{tab:event_registry}
% \end{table}
% \vspace{0.5cm}

% \newpage
% \section{Architektura Komponentowa Systemu}


\subsection{Diagram Komponentów}
Poniższy schemat wizualizuje opisane zależności pomiędzy modułami. Linie przerywane oznaczają komunikację zdarzeniową (Pub/Sub), natomiast linie ciągłe reprezentują bezpośrednie wykorzystanie interfejsów.

\begin{figure}[H]
    \centering
    % Upewnij się, że plik nazywa się dokładnie tak jak tutaj
    \includegraphics[width=1.0\textwidth]{diagram_komponentów_dp.png}
    \caption{Diagram komponentów systemu}
    \label{fig:component_diagram}
\end{figure}

\end{document}

\end{document}


Rules:
Use modern python coding standards.
Don't use emojis.
Don't make mistakes.
Don't create comments.
Use type suggestions everywhere possible.

You will be focusing on implementing the Network and Discovery Module.
@startuml

skinparam classAttributeIconSize 0
skinparam linetype ortho
skinparam nodesep 60
skinparam ranksep 60

' --- EXTERNAL INJECTED DEPENDENCIES ---
package "External Core" {
    class IdentityManager
    class CertificateValidator
    
    interface IBlockchainInterface {
        + get_latest_block_hash(): str
        + get_latest_block_height(): int
        + has_block(hash: str): bool
        + add_block(block_data: dict): void
        + handle_transaction(tx_data: dict): void
        + get_blocks_from(height: int): list[Block]
    }
}

package "Network Module" {

    enum MessageType {
        HANDSHAKE
        TRANSACTION
        BLOCK
        GET_BLOCKS    
        BLOCKS_RESPONSE
    }

    class NetworkMessage {
        - type: MessageType
        - payload: dict
        - signature: str
        + to_json(): str
        + {static} from_json(json_str): NetworkMessage
    }


    interface IConnectionListener {
        + on_message(msg: NetworkMessage, sender: IPeerConnection): void
        + on_disconnect(sender: IPeerConnection): void
        + on_handshake_complete(sender: IPeerConnection): void
    }

    ' --- 3. LOW LEVEL CONNECTION ---

    interface IPeerConnection {
        + remote_height: int
        + remote_hash: str
        + peer_id: str
        + send(msg: NetworkMessage): void
        + close(): void
    }
    
    class PeerConnection {
        - socket: socket
        - state: ConnectionState 
        - out_queue: Queue
        - listener: IConnectionListener
        
        ' Sync Metadata (Set during Handshake)
        + remote_height: int
        + remote_hash: str
        + peer_id: str
        
        + send(msg: NetworkMessage): void
        + close(): void
        - _listen_loop(): void
        - _perform_handshake(): void
    }

    ' --- 4. HIGH LEVEL MANAGEMENT ---

    class PeerManager {
        - peers: Map<peer_id, IPeerConnection>
        - pending_peers: list[IPeerConnection]
        - chain: IBlockchainInterface
        
        + connect_to(ip: str, port: int): void
        + broadcast(msg: NetworkMessage): void
        + send_direct(peer_id: str, msg: NetworkMessage): void
        + get_best_peer(): IPeerConnection
        
        ' Interface Implementation
        + on_message(msg: NetworkMessage, sender: IPeerConnection): void
        + on_handshake_complete(sender: IPeerConnection): void
    }

    class BlockSynchronizer {
        - chain: IBlockchainInterface
        - peers: PeerManager
        - is_syncing: bool
        
        + sync_blockchain(): void
        ' Logic: ask best peer for blocks > my height
        - _request_missing_blocks(peer: IPeerConnection): void 
        + handle_block_response(payload: list): void
    }

    class DiscoveryService {
        - found_peers: Queue
        + start_listener(): void
        + broadcast_presence(): void
        + get_new_peers(): list[(ip, port)]
    }

    ' --- 5. FACADE ---

    class NetworkManager {
        - peer_manager: PeerManager
        - synchronizer: BlockSynchronizer
        - discovery: DiscoveryService
        - chain: IBlockchainInterface
        
        + start(): void
        + broadcast_tx(tx: dict): void   
        + broadcast_block(blk: dict): void
        - _discovery_loop(): void
    }
    
    ' --- RELATIONSHIPS ---

    PeerConnection ..|> IPeerConnection
    PeerConnection --> IConnectionListener : listener
    PeerManager ..|> IConnectionListener
    PeerManager *-- IPeerConnection
    
    NetworkMessage ..> MessageType
    
    NetworkManager o-- IBlockchainInterface : injected
    NetworkManager *-- PeerManager
    NetworkManager *-- BlockSynchronizer
    NetworkManager *-- DiscoveryService
    NetworkManager --> PeerManager : provides chain
    NetworkManager --> BlockSynchronizer : provides chain
    
    BlockSynchronizer --> PeerManager : requests data
    BlockSynchronizer --> IBlockchainInterface : updates chain

    PeerManager o-- IBlockchainInterface : held reference
    
    ' Discovery integration
    NetworkManager ..> DiscoveryService : polls
    NetworkManager ..> PeerManager : feeds IPs
}

@enduml


