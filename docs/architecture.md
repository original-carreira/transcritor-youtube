# 🏗️ Arquitetura do Sistema

## 1. Visão Geral

O sistema é um **transcritor de vídeos do YouTube** baseado em Flask, estruturado como um **monólito modular** com separação clara de responsabilidades.

A arquitetura segue uma divisão em camadas, com foco em:

- desacoplamento
- organização
- facilidade de manutenção
- evolução incremental

---

## 2. Camadas do Sistema

### 🔹 Controller (Flask)

**Arquivo:** `app.py`

Responsabilidades:
- Receber requisições HTTP
- Validar entrada (URL do vídeo)
- Acionar o `TranscriptionService`
- Retornar resposta para a UI

---

### 🔹 Service (Camada de Aplicação)

**Arquivo:** `app/services/transcription_service.py`

Classe principal: `TranscriptionService`

Responsabilidades:
- Orquestrar o fluxo de transcrição
- Extrair `video_id` da URL
- Consultar cache via `CacheRepository`
- Acionar `YouTubeClient` quando necessário
- Processar e normalizar a transcrição
- Montar resposta padronizada

---

### 🔹 Infrastructure

#### 📌 YouTubeClient  
**Arquivo:** `app/clients/youtube_client.py`

Responsabilidades:
- Comunicação com `youtube-transcript-api`
- Buscar transcrição por `video_id`
- Trabalhar com fallback de idiomas
- Retornar dados brutos

---

#### 📌 CacheRepository  
**Arquivo:** `app/repositories/repository.py`

Responsabilidades:
- Ler e escrever no arquivo `historico.json`
- Armazenar transcrições
- Recuperar dados já processados
- Reduzir chamadas externas

---

### 🔹 Export Layer

Local: `app/exporters/`

Componentes:

- `txt_exporter.py`
- `docx_exporter.py`
- `srt_exporter.py`
- `exporter_factory.py`

Responsabilidades:
- Implementar exportação por formato
- Seleção dinâmica via factory
- Receber dados estruturados e gerar arquivos

---

## 3. Fluxo da Aplicação

### Passo a passo:

1. Usuário envia URL do vídeo pela interface
2. Flask (`app.py`) recebe a requisição
3. Controller chama `TranscriptionService`
4. Service extrai o `video_id`
5. Service consulta o `CacheRepository`
6. Se existir cache:
   - retorna dados imediatamente
7. Se não existir:
   - chama `YouTubeClient`
   - recebe transcrição bruta
   - processa e normaliza
   - salva no cache (`historico.json`)
8. Service retorna resposta padronizada
9. Controller envia resposta para UI
10. UI renderiza resultado
11. Usuário pode exportar (TXT, DOCX, SRT)

---

## 4. Estrutura de Dados (Contrato do Service)

O `TranscriptionService` retorna um objeto padronizado:

```json
{
  "text": "string | null",
  "segments": "list | null",
  "source": "string",
  "success": "boolean",
  "error": "string | null",
  "titulo": "string | null",
  "thumbnail": "string | null"
}

# Diagrama de Arquitetura (Camadas)

[ UI (HTML / JS / CSS) ]
            ↓
        [ Flask ]
        (app.py)
            ↓
[ TranscriptionService ]
            ↓
   ┌────────┴────────┐
   ↓                 ↓
[ CacheRepository ]  [ YouTubeClient ]
        ↓
  historico.json

            ↓
      [ Exporters ]
 (TXT / DOCX / SRT)

 # Diagrama de Sequência

 Usuário
  ↓
UI (Browser)
  ↓
Flask (app.py)
  ↓
TranscriptionService
  ↓
CacheRepository ──────→ (verifica cache)
  ↓                      ↓
  ↓               (hit) retorna
  ↓
(miss)
  ↓
YouTubeClient ───────→ YouTube API
  ↓
TranscriptionService (processa)
  ↓
CacheRepository (salva)
  ↓
Flask
  ↓
UI (renderiza)

Contrato

# O contrato do sistema está centrado no retorno do TranscriptionService.

Características:

formato consistente
independente da origem (cache ou API)
pronto para consumo pela UI
reutilizável para exportação

# Responsabilidade dos Componentes
Componente	            Responsabilidade principal
app.py                  Controller HTTP
TranscriptionService	Orquestração e regra de negócio
YouTubeClient	        Integração com YouTube
CacheRepository	        Persistência local (JSON)
Exporters	            Geração de arquivos
UI	                    Interação com usuário


Campos:
text:           texto completo da transcrição
segments:       segmentos temporais (usado para SRT)
source:         origem (cache ou youtube)
success:        status da operação
error:          mensagem de erro, se houver
titulo:         título do vídeo
thumbnail:      URL da thumbnail

Considerações
Arquitetura simples e escalável
Baixo acoplamento entre camadas
Fácil extensão (novos exporters, novos clients)
Ideal para evolução incremental