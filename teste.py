from app.infra.translators.translator_factory import get_translator

translator = get_translator()

resultado = translator.traduzir(
    "Olá mundo",
    source_lang="pt",
    target_lang="en"
)

print(resultado)  # Hello world