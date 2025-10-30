# Exemplo de Uso - Sistema com Validação de Fontes

## 📝 Exemplo 1: Pergunta com Fontes Disponíveis

### Request
```json
POST /ask
{
  "question": "Quais são meus direitos ao comprar um produto com defeito?",
  "category": "Direito do Consumidor",
  "user_context": "Comprei um celular que parou de funcionar após 15 dias",
  "complexity": "simple"
}
```

### Response (Válida - Usa Fontes)
```json
{
  "answer": "Segundo o **CDC - Artigo 18**, quando você compra um produto com defeito, você tem direito a:\n\n1. **Substituição do produto** por outro da mesma espécie\n2. **Restituição do valor pago** (devolução do dinheiro)\n3. **Abatimento proporcional do preço**\n\nNo seu caso, como o celular parou de funcionar em 15 dias, você está dentro do prazo. Conforme o **CDC - Artigo 26**, para produtos duráveis (como celulares) você tem até **90 dias** para reclamar de vícios aparentes.\n\n**Próximos Passos:**\nDirija-se à loja com a nota fiscal e o produto. A loja tem 30 dias para resolver o problema.\n\n**Fontes Consultadas:**\n- CDC - Artigo 18\n- CDC - Artigo 26\n- Lei 8.078/90",
  
  "sources": [
    {
      "title": "CDC - Artigo 18",
      "source": "Lei 8.078/90",
      "relevance_score": 0.95
    },
    {
      "title": "CDC - Artigo 26",
      "source": "Lei 8.078/90",
      "relevance_score": 0.87
    }
  ],
  
  "confidence_score": 88.5,
  "category": "Direito do Consumidor",
  "disclaimer": "⚠️ **IMPORTANTE**: Questões de direito do consumidor podem variar conforme as circunstâncias específicas...",
  "timestamp": "2025-10-30T15:30:00"
}
```

### Logs do Sistema
```
INFO - Validação da resposta: Resposta válida com confiança alta
INFO - Fontes citadas: 2
INFO - Confiança ajustada: 90.00 → 88.50
```

---

## ❌ Exemplo 2: Resposta Inválida (Conhecimento Externo)

### Request
```json
POST /ask
{
  "question": "Como funciona o processo de divórcio?",
  "category": "Direito de Família",
  "complexity": "simple"
}
```

### Response (Inválida - Sem Fontes na Base)
```json
{
  "answer": "Não encontrei informações suficientes nas fontes disponíveis para responder completamente sobre o processo de divórcio.\n\nPara obter orientações precisas sobre seu caso específico, recomendo:\n1. Consultar um advogado especializado em Direito de Família\n2. Procurar a Defensoria Pública (atendimento gratuito)\n3. Buscar informações no site do tribunal da sua região",
  
  "sources": [],
  
  "confidence_score": 15.0,
  "category": "Direito de Família",
  "disclaimer": "⚠️ **IMPORTANTE**: Questões de direito de família envolvem aspectos pessoais...",
  "timestamp": "2025-10-30T15:35:00"
}
```

### Logs do Sistema
```
WARNING - Validação da resposta: Resposta honesta sobre limitação das fontes
INFO - Fontes citadas: 0
INFO - Confiança ajustada: 70.00 → 15.00
```

---

## ⚠️ Exemplo 3: Detecção de Alucinação

### Cenário Hipotético (Sistema ANTES da validação)

```json
{
  "answer": "Segundo o artigo 123, § 4º, inciso II da Lei 99.999/2025, você deve pagar uma multa de R$ 1.234,56 (correspondente a 23,45% do valor) até o dia 15/03/2024. Geralmente, em casos assim, é comum que...",
  
  "confidence_score": 45.0  // REDUZIDO!
}
```

### Logs do Sistema
```
WARNING - Indicadores de alucinação: ['artigos_especificos: 1 ocorrências', 'datas_especificas: 1 ocorrências', 'numeros_muito_precisos: 1 ocorrências', 'percentuais_especificos: 1 ocorrências']
INFO - Confiança ajustada: 90.00 → 45.00
```

---

## ✅ Exemplo 4: Diferentes Níveis de Complexidade

### Simple (Padrão)
```json
{
  "complexity": "simple",
  "answer": "De acordo com o CDC, você pode trocar o produto com defeito. A loja tem que resolver em até 30 dias..."
}
```

### Detailed
```json
{
  "complexity": "detailed",
  "answer": "**Fundamento Legal:**\nO Código de Defesa do Consumidor (Lei 8.078/90), em seu artigo 18, estabelece...\n\n**Prazos:**\n- 30 dias para produtos não duráveis (Art. 26, I)\n- 90 dias para produtos duráveis (Art. 26, II)\n\n**Suas Opções:**\n1. Substituição do produto (Art. 18, § 1º, I)...\n\n**Fontes Consultadas:**\n- CDC - Artigo 18\n- CDC - Artigo 26"
}
```

### Technical
```json
{
  "complexity": "technical",
  "answer": "**Dispositivos Legais Aplicáveis:**\n\nLei nº 8.078/90 (Código de Defesa do Consumidor):\n- Art. 18, caput: Responsabilidade por vícios do produto\n- Art. 18, § 1º, incisos I a III: Opções do consumidor\n- Art. 26, inciso II: Prazo decadencial de 90 dias\n\n**Procedimento:**\n1. Notificação extrajudicial ao fornecedor..."
}
```

---

## 🔧 Testando o Sistema

### 1. Teste com cURL
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Posso trocar um produto com defeito?",
    "category": "Direito do Consumidor",
    "complexity": "simple"
  }'
```

### 2. Teste com Python
```python
import requests

response = requests.post(
    "http://localhost:8000/ask",
    json={
        "question": "Quais meus direitos como consumidor?",
        "category": "Direito do Consumidor",
        "user_context": "Produto veio com defeito",
        "complexity": "detailed"
    }
)

result = response.json()
print(f"Confiança: {result['confidence_score']}")
print(f"Fontes: {len(result['sources'])}")
print(f"Resposta: {result['answer']}")
```

### 3. Verificar Logs
```bash
tail -f logs/rag_service.log | grep -i "validação\|confiança\|alucinação"
```

---

## 📊 Interpretando o Score de Confiança

| Score | Significado | Ação Recomendada |
|-------|-------------|------------------|
| 85-95% | Alta confiança - Resposta bem fundamentada nas fontes | Use a resposta |
| 70-84% | Confiança média - Resposta parcialmente fundamentada | Use com cautela |
| 50-69% | Baixa confiança - Poucos dados nas fontes | Busque mais informações |
| < 50% | Muito baixa - Dados insuficientes ou suspeitos | Não use, consulte profissional |

---

## 🎯 Melhores Práticas

### ✅ DO (Faça)
- Forneça contexto específico no `user_context`
- Escolha a categoria correta
- Use complexidade adequada ao público
- Sempre leia o disclaimer
- Verifique o `confidence_score`

### ❌ DON'T (Não Faça)
- Confiar cegamente em respostas com baixo score
- Ignorar o disclaimer legal
- Usar respostas sem verificar as fontes
- Assumir que o sistema substitui um advogado

---

## 🚀 Próximos Passos

Após receber a resposta:

1. **Score > 80%:** Informação confiável, mas sempre consulte um advogado para casos específicos
2. **Score 50-80%:** Use como orientação inicial, busque mais informações
3. **Score < 50%:** Consulte diretamente um profissional

**Lembre-se:** Este é um sistema de orientação. Para questões específicas e ações legais, sempre consulte um advogado qualificado.
