# chatbot_config.py

from openai import OpenAI
from questions import INITIAL_QUESTIONS

# Klient użyje klucza z OPENAI_API_KEY (ustawionego w systemie)
client = OpenAI()


class ConversationState:
    """
    Przechowuje stan rozmowy dla jednego okna chatu:
    - na którym pytaniu startowym jesteśmy
    - odpowiedzi użytkownika (profil nastroju)
    """
    def __init__(self):
        self.current_index = 0       # indeks w INITIAL_QUESTIONS
        self.answers = {}            # np. {"mood": "...", "energy": "..."}

    def has_more_initial_questions(self) -> bool:
        return self.current_index < len(INITIAL_QUESTIONS)

    def get_current_question_text(self) -> str:
        if self.has_more_initial_questions():
            return INITIAL_QUESTIONS[self.current_index]["text"]
        return ""

    def save_answer_and_advance(self, user_message: str):
        """Zapisuje odpowiedź do aktualnego pytania i przechodzi do następnego."""
        if not self.has_more_initial_questions():
            return
        q = INITIAL_QUESTIONS[self.current_index]
        self.answers[q["id"]] = user_message
        self.current_index += 1


def _call_gpt(prompt: str) -> str:
    """
    Niskopoziomowe wywołanie modelu – używa Chat Completions z gpt-5-mini.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Jesteś asystentem Emotions Chat. "
                        "Rozmawiasz po polsku, pytasz o emocje i pomagasz dobierać filmy. "
                        "Odpowiadasz krótko (1–3 zdania)."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )
        # klasyczna struktura: choices[0].message.content
        return response.choices[0].message.content.strip()

    except Exception as e:
        print("Błąd przy wywołaniu OpenAI:", repr(e))
        return "Przepraszam, coś poszło nie tak po mojej stronie. Spróbuj za chwilę."


def handle_user_message(user_message: str, state: ConversationState) -> str:
    """
    Główna funkcja, której będzie używać GUI.

    Zasada:
    - jeśli wciąż jesteśmy w sekwencji pytań startowych:
        * potraktuj wiadomość jako odpowiedź na aktualne pytanie
        * zapisz ją w stanie
        * zwróć kolejne pytanie ALBO podsumowanie
    - jeśli pytania startowe już zebrane:
        * odpytaj model, przekazując profil użytkownika jako kontekst
    """

    # 1) Czy wciąż zbieramy odpowiedzi na pytania startowe?
    if state.has_more_initial_questions():
        state.save_answer_and_advance(user_message)

        # Jeśli są jeszcze pytania → zadaj kolejne
        if state.has_more_initial_questions():
            return state.get_current_question_text()

        # Jeśli właśnie skończyliśmy wszystkie pytania:
        mood = state.answers.get("mood", "nieznany")
        energy = state.answers.get("energy", "nieznana")
        company = state.answers.get("company", "nieznane")
        genre = state.answers.get("genre", "brak preferencji")

        summary_prompt = (
            "Użytkownik opisał swój nastrój i sytuację.\n"
            f"- Nastrój: {mood}\n"
            f"- Poziom energii: {energy}\n"
            f"- Ogląda: {company}\n"
            f"- Preferencja gatunku: {genre}\n\n"
            "Podziękuj krótko za odpowiedzi, powiedz że to pomoże dobrać film, "
            "i zaproś użytkownika, żeby napisał, na co mniej więcej ma ochotę lub jakie ma oczekiwania."
        )

        return _call_gpt(summary_prompt)

    # 2) Pytania startowe już zebrane → normalna rozmowa z kontekstem profilu

    mood = state.answers.get("mood", "nieznany")
    energy = state.answers.get("energy", "nieznana")
    company = state.answers.get("company", "nieznane")
    genre = state.answers.get("genre", "brak preferencji")

    prompt = (
        "Użytkownik pisze wiadomość w kontekście doboru filmu.\n"
        f"Profil z wywiadu:\n- Nastrój: {mood}\n- Energia: {energy}\n"
        f"- Ogląda: {company}\n- Gatunek: {genre}\n\n"
        f"Aktualna wiadomość użytkownika: {user_message}\n\n"
        "Odpowiedz krótko (1–3 zdania), nawiązując do jego nastroju i sytuacji. "
        "Możesz zadawać dodatkowe pytania o to, na jakie filmy lub motywy ma ochotę."
    )

    return _call_gpt(prompt)


# Prosty test z konsoli (opcjonalnie)
if __name__ == "__main__":
    st = ConversationState()
    print("Test API – napisz coś (exit, aby wyjść):")
    while True:
        msg = input("Ty: ")
        if msg.lower() == "exit":
            break
        print("Bot:", handle_user_message(msg, st))
