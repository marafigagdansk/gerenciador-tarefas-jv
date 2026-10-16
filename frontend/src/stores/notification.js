import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api'

export const useNotificationStore = defineStore('notification', () => {
  const notifications = ref([])
  const unreadCount = ref(0)
  const radarData = ref({
    critical_tasks: [],
    today_tasks: [],
    important_projects: [],
  })
  const browserPermission = ref(
    typeof window !== 'undefined' && 'Notification' in window
      ? Notification.permission
      : 'default'
  )
  const pollingTimer = ref(null)
  const currentPollingCompanyId = ref(null)

  async function requestBrowserPermission() {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      try {
        const perm = await Notification.requestPermission()
        browserPermission.value = perm
        return perm
      } catch (e) {
        console.warn('Erro ao solicitar permissão de notificações:', e)
      }
    }
    return 'default'
  }

  async function fetchNotifications(companyId) {
    if (!companyId) return
    try {
      const res = await api(`/companies/${companyId}/notifications`)
      if (res) {
        notifications.value = res.notifications || []
        unreadCount.value = Number(res.unread_count || 0)

        // Disparo de Browser Push Local para notificações ainda não entregues
        const undelivered = notifications.value.filter(
          (n) => !n.delivered_browser || n.delivered_browser === 0
        )

        if (
          undelivered.length > 0 &&
          typeof window !== 'undefined' &&
          'Notification' in window &&
          Notification.permission === 'granted'
        ) {
          const idsToMark = []
          for (const notif of undelivered) {
            try {
              new Notification(notif.title, {
                body: notif.message,
                icon: '/vite.svg',
                tag: `notif-${notif.id}`,
              })
              idsToMark.push(notif.id)
            } catch (err) {
              console.warn('Erro ao disparar notificação local no navegador:', err)
            }
          }

          if (idsToMark.length > 0) {
            // Marca como delivered no backend para evitar repetição no F5
            try {
              await api('/notifications/mark-browser-delivered', {
                method: 'POST',
                body: { notification_ids: idsToMark },
              })
              // Atualiza localmente
              notifications.value.forEach((n) => {
                if (idsToMark.includes(n.id)) {
                  n.delivered_browser = true
                }
              })
            } catch (e) {
              console.warn('Erro ao marcar browser delivered:', e)
            }
          }
        }
      }
    } catch (err) {
      console.warn('Aviso: falha ao buscar notificações:', err)
    }
  }

  async function fetchOverviewRadar(companyId) {
    if (!companyId) return
    try {
      const res = await api(`/companies/${companyId}/overview-radar`)
      if (res) {
        radarData.value = {
          critical_tasks: res.critical_tasks || [],
          today_tasks: res.today_tasks || [],
          important_projects: res.important_projects || [],
        }
      }
    } catch (err) {
      console.warn('Aviso: falha ao buscar overview-radar:', err)
    }
  }

  function startPolling(companyId) {
    if (!companyId) return
    if (currentPollingCompanyId.value === companyId && pollingTimer.value) {
      // Já está em polling na mesma empresa, apenas sincroniza
      fetchNotifications(companyId)
      fetchOverviewRadar(companyId)
      return
    }

    stopPolling()
    currentPollingCompanyId.value = companyId

    // Executa imediatamente
    fetchNotifications(companyId)
    fetchOverviewRadar(companyId)

    // Intervalo de 60 segundos
    pollingTimer.value = setInterval(() => {
      if (currentPollingCompanyId.value) {
        fetchNotifications(currentPollingCompanyId.value)
        fetchOverviewRadar(currentPollingCompanyId.value)
      }
    }, 60000)
  }

  function stopPolling() {
    if (pollingTimer.value) {
      clearInterval(pollingTimer.value)
      pollingTimer.value = null
    }
    currentPollingCompanyId.value = null
  }

  async function markAsRead(id) {
    if (!id) return
    try {
      await api(`/notifications/${id}/read`, { method: 'POST' })
      const item = notifications.value.find((n) => n.id === id)
      if (item && !item.is_read) {
        item.is_read = true
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
    } catch (err) {
      console.warn('Erro ao marcar notificação como lida:', err)
    }
  }

  async function markAllAsRead(companyId) {
    if (!companyId) return
    try {
      await api(`/companies/${companyId}/notifications/read-all`, { method: 'POST' })
      notifications.value.forEach((n) => {
        n.is_read = true
      })
      unreadCount.value = 0
    } catch (err) {
      console.warn('Erro ao marcar todas notificações como lidas:', err)
    }
  }

  return {
    notifications,
    unreadCount,
    radarData,
    browserPermission,
    requestBrowserPermission,
    fetchNotifications,
    fetchOverviewRadar,
    startPolling,
    stopPolling,
    markAsRead,
    markAllAsRead,
  }
})
