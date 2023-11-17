import os
import re
import sys

def fix_html_tags(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Znajdź wszystkie wystąpienia otwierającego tagu <b
    matches = re.finditer(r'<b\s', content)

    # Iteruj przez wszystkie znalezione dopasowania
    for match in matches:
        # Znajdź pozycję początkową i końcową tagu <b
        start = match.start()
        end = match.end()

        # Sprawdź, czy tag <b jest już otwarty
        if content[end:end + 1] != '>':
            # Zamień otwierający tag <b na <b>
            content = content[:start] + '<b>' + content[end:]

    # Zamień ewentualne podzielone tagi <b i> na <b>i</b>
    content = re.sub(r'<b\s.*?\n.*?<p class="s">', '<b>', content)

    # Usuń drugi wariant, jeśli znajduje się bezpośrednio pod pierwszym
    content = re.sub(r'(<p class="s">.*?</p>)\n<p><b><p class="s">.*?</p>', r'\1', content)

    # Zapisz zmodyfikowany content z powrotem do pliku
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def fix_html_files_in_directory(directory):
    # Sprawdź każdy plik w danym katalogu
    for filename in os.listdir(directory):
        if filename.endswith(".html"):
            file_path = os.path.join(directory, filename)
            fix_html_tags(file_path)

if __name__ == "__main__":
    # Sprawdź, czy podano ścieżkę jako argument
    if len(sys.argv) != 2:
        print("Podaj ścieżkę do katalogu jako argument.")
        sys.exit(1)

    # Podaj ścieżkę do katalogu z argumentu
    directory_path = sys.argv[1]

    # Wywołaj funkcję naprawiającą tagi HTML w plikach w danym katalogu
    fix_html_files_in_directory(directory_path)

    print("Naprawa zakończona.")
