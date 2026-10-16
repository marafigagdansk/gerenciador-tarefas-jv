<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Calendar, ChevronLeft, ChevronRight, X, Clock, CalendarCheck } from 'lucide-vue-next'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: 'Selecione uma data' },
  disabled: { type: Boolean, default: false },
  id: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const isOpen = ref(false)
const containerRef = ref(null)

// Data de visualização do calendário (ano e mês)
const viewYear = ref(new Date().getFullYear())
const viewMonth = ref(new Date().getMonth()) // 0-indexed (0 = Jan, 11 = Dez)

const MESES = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
]

const DIAS_SEMANA = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']

// Inicializa a visão com a data atual selecionada ou hoje
watch(() => props.modelValue, (val) => {
  if (val && /^\d{4}-\d{2}-\d{2}$/.test(val)) {
    const [y, m] = val.split('-').map(Number)
    viewYear.value = y
    viewMonth.value = m - 1
  }
}, { immediate: true })

function toggleOpen() {
  if (props.disabled) return
  if (!isOpen.value) {
    if (props.modelValue && /^\d{4}-\d{2}-\d{2}$/.test(props.modelValue)) {
      const [y, m] = props.modelValue.split('-').map(Number)
      viewYear.value = y
      viewMonth.value = m - 1
    } else {
      const hoje = new Date()
      viewYear.value = hoje.getFullYear()
      viewMonth.value = hoje.getMonth()
    }
  }
  isOpen.value = !isOpen.value
}

function prevMonth() {
  if (viewMonth.value === 0) {
    viewMonth.value = 11
    viewYear.value--
  } else {
    viewMonth.value--
  }
}

function nextMonth() {
  if (viewMonth.value === 11) {
    viewMonth.value = 0
    viewYear.value++
  } else {
    viewMonth.value++
  }
}

function pad(n) {
  return String(n).padStart(2, '0')
}

function toIso(year, month, day) {
  return `${year}-${pad(month + 1)}-${pad(day)}`
}

const hojeIso = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
})

// Gera a grade de dias (incluindo dias do mês anterior e próximo para completar as semanas)
const calendarDays = computed(() => {
  const year = viewYear.value
  const month = viewMonth.value

  const firstDayOfWeek = new Date(year, month, 1).getDay()
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const daysInPrevMonth = new Date(year, month, 0).getDate()

  const list = []

  // Dias do mês anterior
  for (let i = firstDayOfWeek - 1; i >= 0; i--) {
    const dayNum = daysInPrevMonth - i
    const prevM = month === 0 ? 11 : month - 1
    const prevY = month === 0 ? year - 1 : year
    list.push({
      day: dayNum,
      month: prevM,
      year: prevY,
      iso: toIso(prevY, prevM, dayNum),
      isCurrentMonth: false,
    })
  }

  // Dias do mês atual
  for (let d = 1; d <= daysInMonth; d++) {
    list.push({
      day: d,
      month,
      year,
      iso: toIso(year, month, d),
      isCurrentMonth: true,
    })
  }

  // Dias do próximo mês para fechar a última linha (múltiplo de 7)
  const remaining = 7 - (list.length % 7)
  if (remaining < 7) {
    for (let d = 1; d <= remaining; d++) {
      const nextM = month === 11 ? 0 : month + 1
      const nextY = month === 11 ? year + 1 : year
      list.push({
        day: d,
        month: nextM,
        year: nextY,
        iso: toIso(nextY, nextM, d),
        isCurrentMonth: false,
      })
    }
  }

  return list
})

function selectDate(iso) {
  emit('update:modelValue', iso)
  isOpen.value = false
}

function clearDate(e) {
  if (e) e.stopPropagation()
  emit('update:modelValue', '')
  isOpen.value = false
}

function setShortcut(daysOffset) {
  const d = new Date()
  d.setDate(d.getDate() + daysOffset)
  const iso = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
  emit('update:modelValue', iso)
  viewYear.value = d.getFullYear()
  viewMonth.value = d.getMonth()
  isOpen.value = false
}

const formattedDisplay = computed(() => {
  if (!props.modelValue) return ''
  const clean = props.modelValue.split('T')[0]
  const parts = clean.split('-')
  if (parts.length === 3) {
    const dia = parts[2]
    const mesIndex = Number(parts[1]) - 1
    const ano = parts[0]
    const mesAbrev = MESES[mesIndex] ? MESES[mesIndex].slice(0, 3) : parts[1]
    return `${dia} de ${mesAbrev}. de ${ano}`
  }
  return props.modelValue
})

function handleClickOutside(e) {
  if (containerRef.value && !containerRef.value.contains(e.target)) {
    isOpen.value = false
  }
}

function handleKeydown(e) {
  if (e.key === 'Escape' && isOpen.value) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('pointerdown', handleClickOutside)
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('pointerdown', handleClickOutside)
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div ref="containerRef" class="custom-datepicker-container">
    <!-- Gatilho do DatePicker -->
    <button
      :id="id"
      type="button"
      class="datepicker-trigger"
      :class="{ 'has-value': Boolean(modelValue), 'is-open': isOpen, 'is-disabled': disabled }"
      :disabled="disabled"
      @click="toggleOpen"
      :aria-expanded="isOpen"
      aria-haspopup="dialog"
    >
      <div class="trigger-content">
        <Calendar :size="16" class="calendar-icon" :class="{ 'icon-active': Boolean(modelValue) }" />
        <span v-if="modelValue" class="date-text">{{ formattedDisplay }}</span>
        <span v-else class="placeholder-text">{{ placeholder }}</span>
      </div>

      <div class="trigger-actions">
        <span
          v-if="modelValue && !disabled"
          class="btn-clear"
          title="Limpar data"
          aria-label="Limpar data"
          @click.stop="clearDate"
        >
          <X :size="14" />
        </span>
      </div>
    </button>

    <!-- Popover Flutuante do Calendário -->
    <transition name="popover-fade">
      <div v-if="isOpen" class="datepicker-popover" role="dialog" aria-modal="true">
        <!-- Barra de atalhos rápidos -->
        <div class="quick-shortcuts">
          <button type="button" class="shortcut-pill" @click="setShortcut(0)">Hoje</button>
          <button type="button" class="shortcut-pill" @click="setShortcut(1)">Amanhã</button>
          <button type="button" class="shortcut-pill" @click="setShortcut(7)">+7 dias</button>
          <button v-if="modelValue" type="button" class="shortcut-pill clear" @click="clearDate">Limpar</button>
        </div>

        <!-- Cabeçalho do mês e navegação -->
        <div class="calendar-header">
          <button type="button" class="nav-btn" @click="prevMonth" title="Mês anterior" aria-label="Mês anterior">
            <ChevronLeft :size="18" />
          </button>
          <span class="month-year-label">
            <strong>{{ MESES[viewMonth] }}</strong> {{ viewYear }}
          </span>
          <button type="button" class="nav-btn" @click="nextMonth" title="Próximo mês" aria-label="Próximo mês">
            <ChevronRight :size="18" />
          </button>
        </div>

        <!-- Cabeçalho dos dias da semana -->
        <div class="weekdays-grid">
          <span v-for="d in DIAS_SEMANA" :key="d" class="weekday-cell">{{ d }}</span>
        </div>

        <!-- Grade dos dias -->
        <div class="days-grid">
          <button
            v-for="item in calendarDays"
            :key="item.iso"
            type="button"
            class="day-cell"
            :class="{
              'is-current-month': item.isCurrentMonth,
              'is-other-month': !item.isCurrentMonth,
              'is-today': item.iso === hojeIso,
              'is-selected': item.iso === modelValue,
            }"
            @click="selectDate(item.iso)"
          >
            <span>{{ item.day }}</span>
            <span v-if="item.iso === hojeIso && item.iso !== modelValue" class="today-dot"></span>
          </button>
        </div>

        <!-- Rodapé elegante com feedback -->
        <div class="calendar-footer">
          <span v-if="modelValue" class="footer-info">
            <CalendarCheck :size="13" />
            <span>Selecionado: <strong>{{ formattedDisplay }}</strong></span>
          </span>
          <span v-else class="footer-info text-muted">
            <Clock :size="13" />
            <span>Nenhuma data definida</span>
          </span>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.custom-datepicker-container {
  position: relative;
  width: 100%;
}

.datepicker-trigger {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.62rem 0.85rem;
  background: var(--bg-input, #FFFFFF);
  border: 1px solid var(--border-color, #E7E5E4);
  border-radius: var(--radius-sm, 6px);
  color: var(--text-main, #1C1917);
  font-family: inherit;
  font-size: 0.92rem;
  text-align: left;
  cursor: pointer;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.02);
  transition: all 0.15s ease;
  min-height: 40px;
}

.datepicker-trigger:hover:not(:disabled) {
  border-color: var(--border-color-hover, #D6D3D1);
  background: #FAFAF9;
}

.datepicker-trigger.is-open {
  border-color: var(--primary, #0F766E);
  box-shadow: 0 0 0 2px var(--primary-glow, rgba(15, 118, 110, 0.18));
  background: #FFFFFF;
}

.datepicker-trigger.is-disabled {
  opacity: 0.6;
  background: #F5F5F4;
  cursor: not-allowed;
}

.trigger-content {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.calendar-icon {
  color: var(--text-subtle, #A8A29E);
  flex-shrink: 0;
  transition: color 0.15s;
}

.calendar-icon.icon-active {
  color: var(--primary, #0F766E);
}

.date-text {
  font-weight: 500;
  color: var(--text-main, #1C1917);
}

.placeholder-text {
  color: var(--text-muted, #78716C);
}

.trigger-actions {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.btn-clear {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  color: var(--text-muted, #78716C);
  background: #F5F5F4;
  transition: all 0.15s;
}

.btn-clear:hover {
  background: #E7E5E4;
  color: var(--danger, #B91C1C);
}

/* Popover do Calendário */
.datepicker-popover {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: 70;
  width: 310px;
  background: #FFFFFF;
  border: 1px solid var(--border-color, #E7E5E4);
  border-radius: var(--radius-md, 10px);
  box-shadow: var(--shadow-modal, 0 10px 25px -5px rgba(0, 0, 0, 0.12));
  padding: 0.85rem;
  user-select: none;
}

/* Atalhos Rápidos */
.quick-shortcuts {
  display: flex;
  gap: 0.35rem;
  padding-bottom: 0.75rem;
  margin-bottom: 0.75rem;
  border-bottom: 1px solid var(--border-color, #E7E5E4);
  flex-wrap: wrap;
}

.shortcut-pill {
  border: 1px solid var(--border-color, #E7E5E4);
  background: #FAFAF9;
  color: var(--text-main, #1C1917);
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.55rem;
  border-radius: 999px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.shortcut-pill:hover {
  background: #F0FDFA;
  border-color: #99F6E4;
  color: #0F766E;
}

.shortcut-pill.clear {
  color: var(--danger, #B91C1C);
  background: #FEF2F2;
  border-color: #FECACA;
  margin-left: auto;
}

.shortcut-pill.clear:hover {
  background: #FEE2E2;
}

/* Cabeçalho do Mês */
.calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.6rem;
}

.month-year-label {
  font-size: 0.95rem;
  color: var(--text-main, #1C1917);
}

.month-year-label strong {
  font-weight: 700;
  color: var(--primary, #0F766E);
}

.nav-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm, 6px);
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-muted, #78716C);
  cursor: pointer;
  transition: all 0.15s;
}

.nav-btn:hover {
  background: #F5F5F4;
  color: var(--text-main, #1C1917);
  border-color: var(--border-color, #E7E5E4);
}

/* Dias da Semana */
.weekdays-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
  margin-bottom: 0.35rem;
  text-align: center;
}

.weekday-cell {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-muted, #78716C);
  padding: 0.3rem 0;
  letter-spacing: 0.05em;
}

/* Grade dos Dias */
.days-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 3px;
}

.day-cell {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 34px;
  border-radius: 6px;
  border: 1px solid transparent;
  background: transparent;
  font-size: 0.85rem;
  font-family: inherit;
  font-weight: 500;
  cursor: pointer;
  color: var(--text-main, #1C1917);
  transition: all 0.15s ease;
}

.day-cell.is-other-month {
  color: var(--text-subtle, #D6D3D1);
}

.day-cell.is-current-month:hover {
  background: #F0FDFA;
  color: #0F766E;
  border-color: #99F6E4;
}

.day-cell.is-today {
  font-weight: 700;
  color: var(--primary, #0F766E);
}

.today-dot {
  position: absolute;
  bottom: 3px;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--primary, #0F766E);
}

.day-cell.is-selected {
  background: var(--primary, #0F766E) !important;
  color: #FFFFFF !important;
  font-weight: 700;
  box-shadow: 0 1px 4px rgba(15, 118, 110, 0.3);
}

.day-cell.is-selected .today-dot {
  background: #FFFFFF;
}

/* Rodapé */
.calendar-footer {
  margin-top: 0.75rem;
  padding-top: 0.6rem;
  border-top: 1px solid var(--border-color, #E7E5E4);
  font-size: 0.78rem;
}

.footer-info {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: #0F766E;
}

.footer-info.text-muted {
  color: var(--text-muted, #78716C);
}

/* Animação */
.popover-fade-enter-active,
.popover-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.popover-fade-enter-from,
.popover-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.98);
}
</style>
