🎥 YouTube Transcriber
1. Descrição

O YouTube Transcriber é uma aplicação web baseada em Flask que realiza a extração, processamento e exportação de transcrições de vídeos do YouTube.

O projeto foi estruturado com foco em:

Separação clara de responsabilidades
Baixo acoplamento entre camadas
Facilidade de manutenção e evolução

A arquitetura segue um modelo de monólito modular com camadas bem definidas, permitindo escalar o sistema sem perda de organização.

2. Funcionalidades
Extração de transcrições de vídeos do YouTube
Suporte a múltiplos idiomas (pt, pt-BR, en)
Processamento e normalização do conteúdo textual
Cache persistente em arquivo JSON
Histórico de transcrições acessível pela interface
Exportação de transcrições nos formatos:
TXT
DOCX
SRT
Interface web com:
Loading visual
Scroll para textos longos
Botão de cópia rápida
Histórico persistente
3. Tecnologias Utilizadas
Backend
Python
Flask
Bibliotecas
youtube-transcript-api
python-docx
Frontend
HTML5
CSS3
JavaScript (vanilla)
Persistência
JSON (arquivo local)
4. Arquitetura do Sistema

O sistema segue uma arquitetura em camadas com responsabilidades bem definidas:

UI (HTML/CSS/JS)
        ↓
app.py (Flask Controller)
        ↓
TranscriptionService (Regra de Negócio)
        ↓
YouTubeClient (Integração externa)
        ↓
Repository (Persistência / Cache)
        ↓
Exporters (Strategy Pattern)

5. Componentes e Responsabilidades
🔹 app.py
Ponto de entrada da aplicação Flask
Define rotas HTTP
Orquestra chamadas ao TranscriptionService
Retorna dados para a UI
🔹 TranscriptionService

Arquivo: app/services/transcription_service.py

Responsabilidades:

Coordenar o fluxo de transcrição
Extrair video_id a partir da URL
Consultar cache via Repository
Acionar YouTubeClient quando necessário
Normalizar e estruturar os dados
Retornar resposta padronizada
🔹 YouTubeClient

Arquivo: app/clients/youtube_client.py

Responsabilidades:

Comunicação com a biblioteca youtube-transcript-api
Buscar transcrições por video_id
Aplicar fallback de idiomas
Retornar dados crus para o service
🔹 Repository

Arquivo: app/repositories/repository.py

Responsabilidades:

Gerenciar leitura e escrita no historico.json
Armazenar transcrições
Recuperar dados em cache
Evitar requisições repetidas ao YouTube
🔹 Exporters (Strategy Pattern)

Local: app/exporters/

Implementações:
txt_exporter.py
docx_exporter.py
srt_exporter.py

Responsabilidades:

Cada classe implementa um formato de exportação específico
Recebem dados estruturados e geram arquivos
Factory:

Arquivo: exporter_factory.py

Responsabilidade:

Selecionar dinamicamente o exporter correto com base no formato

6. Fluxo da Aplicação
Usuário insere a URL do vídeo na interface
Requisição é enviada ao app.py
TranscriptionService executa:
Extrai video_id
Consulta cache (Repository)
Se não existir:
YouTubeClient busca a transcrição
Dados são processados
Resultado é salvo no historico.json
Resultado retorna para a UI
Usuário pode:
Visualizar
Copiar
Exportar em diferentes formatos

7. Estrutura de Pastas
project-root/
│
├── app/
│   ├── clients/
│   │   └── youtube_client.py
│   │
│   ├── exporters/
│   │   ├── docx_exporter.py
│   │   ├── txt_exporter.py
│   │   ├── srt_exporter.py
│   │   └── exporter_factory.py
│   │
│   ├── repositories/
│   │   └── repository.py
│   │
│   └── services/
│       └── transcription_service.py
│
├── static/
│   ├── script.js
│   └── style.css
│
├── templates/
│   └── index.html
│
├── historico.json        # Cache persistente
├── app.py                # Entry point Flask
├── requirements.txt
├── README.md
|-  Arquitecture.md
|-  Decisions.md


8. Persistência (historico.json)

O sistema utiliza um arquivo local como cache:

{
  "video_id": "string",
  "url": "string",
  "titulo": "string",
  "thumbnail": "string",
  "transcricao": "string"
}
Objetivos:
Reduzir chamadas externas
Melhorar performance
Manter histórico acessível

9. Como Executar o Projeto
Pré-requisitos
Python 3.10+
pip
Instalação
git clone https://github.com/seu-usuario/youtube-transcriber.git
cd youtube-transcriber

python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
Execução
python app.py

Acesse:

http://localhost:5000

10. Exemplo de Uso
Acesse a aplicação
Insira a URL de um vídeo do YouTube
Clique em Transcrever
Aguarde o processamento
Utilize:
Copiar texto
Exportar (TXT, DOCX, SRT)
Histórico

11. Roadmap Futuro
Interface com filtros no histórico
Busca por título ou conteúdo
Exportação em PDF
Suporte a múltiplos idiomas configuráveis
Deploy com Docker
Pipeline assíncrono (fila de processamento)

12. Observações
Nem todos os vídeos possuem transcrição disponível
A disponibilidade depende do YouTube
Pode ser necessário uso de VPN em alguns casos
O sistema não gera transcrição — apenas consome as disponíveis