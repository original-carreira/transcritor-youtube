# 🎥 Transcritor de Vídeos do YouTube

Aplicação desenvolvida em Python com Flask para obter, limpar e exportar transcrições de vídeos do YouTube.

---

# 🚀 Funcionalidades

* 🔗 Inserção de URL de vídeo do YouTube
* 📝 Extração automática de transcrição
* 🧹 Limpeza e organização do texto
* 💾 Exportação:

  * TXT
  * Word (.docx)
* 📋 Copiar texto com um clique
* 🖼️ Exibição de thumbnail do vídeo
* 📚 Histórico de transcrições (cache local)
* ⚡ Cache inteligente (evita requisições repetidas)
* 🧼 Limpeza manual do histórico
* 💻 Executável (.exe)
* 📦 Instalador profissional (Inno Setup)

---

# 🧠 Tecnologias Utilizadas

* Python 3
* Flask
* HTML / CSS / JavaScript
* PyInstaller
* Inno Setup
* JSON (armazenamento local)

---

# 📁 Estrutura do Projeto

```
projeto/
│
├── app.py
├── transcript.py
├── requirements.txt
├── .gitignore
│
├── static/
│   ├── style.css
│   └── script.js
│
├── templates/
│   └── index.html
│
├── dist/                 # executável (gerado)
├── build/                # build (gerado)
│
├── installer/
│   ├── setup.iss
│   ├── icon.ico
│   └── output/           # instalador (gerado)
```

---

# ⚙️ Execução em Desenvolvimento

Ativar ambiente virtual:

```
venv\Scripts\activate
```

Executar aplicação:

```
python app.py
```

Acessar:

```
http://127.0.0.1:5000
```

---

# ⛔ Encerramento do Servidor

Para parar a aplicação no terminal:

```
CTRL + C
```

---

# 🔁 Fluxo da Aplicação (IMPORTANTE)

## Método GET

* Carrega a página inicial
* Não processa dados
* Estado inicial vazio

## Método POST

* Envia a URL do formulário
* Processa a transcrição
* Retorna resultado para o template

### ⚠️ Aprendizado importante

* GET → leitura / carregamento
* POST → envio de dados / processamento
* Separar bem essas responsabilidades evita bugs

---

# 🧠 Lógica de Processamento

1. Recebe URL
2. Extrai ID do vídeo
3. Verifica cache (JSON)
4. Se existir → retorna instantaneamente
5. Se não:

   * busca transcrição
   * limpa texto
   * salva no cache
6. Retorna resultado para o frontend

---

# 💾 Cache (Histórico)

Arquivo salvo em:

```
AppData/Local/TranscritorYouTube/historico.json
```

## Vantagens:

* evita bloqueio de IP
* melhora performance
* persistência local

---

# 🧪 Funcionalidades de UX

* Loading ao processar
* Botão copiar
* Botão nova transcrição
* Histórico clicável
* Limpeza de histórico
* Layout responsivo

---

# 🛠️ Geração do Executável

```
pyinstaller --onefile --add-data "templates;templates" --add-data "static;static" app.py
```

Saída:

```
dist/TranscritorYouTube.exe
```

---

# 📦 Criação do Instalador

Ferramenta: Inno Setup

Script:

```
installer/setup.iss
```

Compilar:

```
Compile → gera instalador
```

Saída:

```
installer/output/TranscritorYouTube.exe
```

---

# ⚠️ Problemas Importantes Resolvidos

## 🔹 Bloqueio de IP

Solução: cache local

## 🔹 Arquivos no dist

Solução: mover para AppData

## 🔹 Navegador abrindo cedo

Solução: verificar porta ativa antes de abrir

## 🔹 Desinstalação incompleta

Solução:

* CloseApplications
* UninstallDelete

---

# 🧠 Aprendizados (Ponto Mais Importante)

## Backend

* Estrutura Flask
* Rotas GET/POST
* Separação de responsabilidades

## Frontend

* HTML organizado
* CSS separado
* JS modular

## Arquitetura

* Cache persistente
* Organização de código
* separação backend/frontend

## Engenharia

* Git e versionamento
* .gitignore correto
* estrutura de projeto

## Distribuição

* PyInstaller
* executável
* instalador
* comportamento do Windows

---

# 🏷️ Versionamento

Versão atual:

```
v1.0
```

Tipo:

```
release estável distribuível
```

---

# 📌 Status do Projeto

```
✔ Completo (v1.0)
✔ Funcional
✔ Instalável
✔ Distribuível
```

---

# 🚀 Próximos Passos (Futuro)

* Interface mais avançada
* Versão web (deploy)
* Banco de dados
* Autenticação
* Atualizações automáticas

---

# 👤 Autor

Victor Carreira

---

# 📄 Licença

Uso pessoal / educacional
