
---

# 📄 decisions.md

```markdown
# 🧠 Decisões Arquiteturais

Este documento registra as principais decisões técnicas do projeto, incluindo contexto, decisão e consequências.

---

## 1. Uso de Flask

### Contexto
Necessidade de um backend simples com integração direta com UI.

### Decisão
Utilizar Flask como framework principal.

### Consequência
- Simplicidade de implementação
- Baixa curva de aprendizado
- Menor overhead comparado a frameworks maiores
- Menor estrutura nativa (exige organização manual)

---

## 2. Uso de JSON para Cache

### Contexto
Necessidade de persistência leve sem complexidade de banco de dados.

### Decisão
Utilizar arquivo `historico.json` como cache local.

### Consequência
- Implementação simples
- Fácil inspeção manual dos dados
- Não escalável para alto volume
- Sem controle de concorrência

---

## 3. Separação em Camadas

### Contexto
Evitar código acoplado e difícil de manter.

### Decisão
Dividir o sistema em:
- Controller
- Service
- Infrastructure
- Export

### Consequência
- Código mais organizado
- Melhor testabilidade
- Facilidade de evolução
- Leve aumento de complexidade estrutural

---

## 4. Criação do TranscriptionService

### Contexto
Necessidade de centralizar regras de negócio.

### Decisão
Criar uma camada de serviço dedicada.

### Consequência
- Lógica centralizada
- Controller simplificado
- Maior reutilização de código

---

## 5. Isolamento do YouTubeClient

### Contexto
Integração com serviço externo (YouTube).

### Decisão
Isolar acesso à API em uma classe dedicada.

### Consequência
- Baixo acoplamento
- Facilidade de substituição futura
- Melhor testabilidade (mock)

---

## 6. Export Desacoplado

### Contexto
Necessidade de suportar múltiplos formatos.

### Decisão
Implementar exporters separados com factory.

### Consequência
- Fácil adição de novos formatos
- Código organizado por responsabilidade
- Aplicação do padrão Strategy

---

## 7. UI Desacoplada do Backend

### Contexto
Evitar mistura de lógica de negócio com apresentação.

### Decisão
Separar claramente frontend (JS/HTML/CSS) do backend.

### Consequência
- Maior clareza de responsabilidades
- Melhor experiência de manutenção
- Possibilidade futura de SPA ou API dedicada

---

## 8. Uso de Branch para Refatoração

### Contexto
Refatoração estrutural significativa.

### Decisão
Realizar refatoração em branch isolada.

### Consequência
- Segurança no desenvolvimento
- Possibilidade de rollback
- Histórico limpo de mudanças

---

## 9. Limitação: Uso de VPN

### Contexto
Bloqueios regionais no acesso a transcrições do YouTube.

### Decisão
Aceitar a limitação externa (não controlável pelo sistema).

### Consequência
- Necessidade eventual de VPN
- Dependência de fatores externos
- Impacto na experiência do usuário

---