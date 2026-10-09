<script setup>
const props = defineProps({
  empresa: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['select', 'delete'])

function formatarData(dataStr) {
  if (!dataStr) return ''
  try {
    const d = new Date(dataStr + 'Z')
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' })
  } catch {
    return dataStr
  }
}
</script>

<template>
  <div class="empresa-card" @click="emit('select', empresa)">
    <div class="card-header">
      <div class="empresa-icon">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
          <path d="M12 7V3H2v18h20V7H12zM6 19H4v-2h2v2zm0-4H4v-2h2v2zm0-4H4V9h2v2zm0-4H4V5h2v2zm4 12H8v-2h2v2zm0-4H8v-2h2v2zm0-4H8V9h2v2zm0-4H8V5h2v2zm10 12h-8v-2h2v-2h-2v-2h2v-2h-2V9h8v10zm-2-8h-2v2h2v-2zm0 4h-2v2h2v-2z"/>
        </svg>
      </div>
      <button 
        class="btn-delete" 
        title="Remover empresa"
        @click.stop="emit('delete', empresa.id)"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
          <polyline points="3 6 5 6 21 6"></polyline>
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
        </svg>
      </button>
    </div>

    <div class="card-body">
      <h3 class="empresa-nome" :title="empresa.nome">{{ empresa.nome }}</h3>
      <div class="empresa-doc-badge">
        <span class="doc-label">{{ empresa.documento.length > 14 ? 'CNPJ' : 'CPF' }}</span>
        <span class="doc-val">{{ empresa.documento }}</span>
      </div>
    </div>

    <div class="card-footer">
      <span class="data-cadastro">Cadastrado em: {{ formatarData(empresa.criado_em) }}</span>
      <span class="btn-acessar">
        Entrar &rarr;
      </span>
    </div>
  </div>
</template>

<style scoped>
.empresa-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  cursor: pointer;
  transition: transform 0.15s ease, border-color 0.15s ease, background-color 0.15s ease, box-shadow 0.15s ease;
  min-height: 170px;
  will-change: transform;
}

.empresa-card:hover {
  transform: translateY(-3px);
  background: var(--bg-card-hover);
  border-color: var(--border-color-hover);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empresa-icon {
  width: 38px;
  height: 38px;
  background: rgba(99, 102, 241, 0.12);
  color: var(--primary);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-delete {
  background: transparent;
  border: none;
  color: var(--text-subtle);
  cursor: pointer;
  padding: 6px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.15s ease, background-color 0.15s ease;
}

.btn-delete:hover {
  color: var(--danger);
  background: rgba(239, 68, 68, 0.1);
}

.card-body {
  margin: 1rem 0;
}

.empresa-nome {
  font-size: 1.1rem;
  font-weight: 600;
  color: #fff;
  margin-bottom: 0.5rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empresa-doc-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.06);
  padding: 0.25rem 0.6rem;
  border-radius: 4px;
  font-size: 0.8rem;
  color: var(--text-muted);
}

.doc-label {
  font-weight: 700;
  color: var(--primary);
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 0.8rem;
  color: var(--text-subtle);
}

.btn-acessar {
  color: var(--primary);
  font-weight: 600;
  transition: transform 0.15s ease;
}

.empresa-card:hover .btn-acessar {
  transform: translateX(3px);
}
</style>
