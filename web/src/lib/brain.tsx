import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import { loadConnectome, Sim, type Connectome } from './connectome'

interface BrainCtx { conn: Connectome | null; sim: Sim | null; tick: number }
const Ctx = createContext<BrainCtx>({ conn: null, sim: null, tick: 0 })
// 소비자가 화면에 있는 동안만 커넥텀을 받고 시뮬레이터를 돌리도록, 사용 요청을 세는 함수를 따로 내려 줍니다.
const RequestCtx = createContext<() => () => void>(() => () => {})

// 앱 전체에서 커넥텀 하나, 시뮬레이터 하나를 공유한다. 약 30Hz 로 진행.
// useBrain() 을 쓰는 컴포넌트가 하나도 없는 화면(대문 등)에서는 내려받지도, 돌리지도 않습니다.
export function BrainProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<BrainCtx>({ conn: null, sim: null, tick: 0 })
  const [users, setUsers] = useState(0)
  const simRef = useRef<Sim | null>(null)

  const request = useCallback(() => {
    setUsers((n) => n + 1)
    return () => setUsers((n) => n - 1)
  }, [])

  const active = users > 0
  useEffect(() => {
    if (!active) return
    let alive = true
    let timer = 0
    let uiTick = 0
    loadConnectome().then((conn) => {
      if (!alive) return
      const sim = simRef.current ?? new Sim(conn)
      if (!simRef.current) {
        simRef.current = sim
        ;(window as unknown as { __fv: Sim }).__fv = sim
        setState({ conn, sim, tick: sim.t })
      }
      // 기저 활동: 데이터 스트림이 조용히 흘러 들어오는 상태
      let last = performance.now()
      const loop = () => {
        if (!alive) return
        const now = performance.now()
        if (now - last > 30) {
          last = now
          if (sim.t % 45 === 0) sim.stimulate('channel', ['faers', 'literature', 'trials', 'label', 'digital'][Math.floor(Math.random() * 5)], 0.55, 5)
          sim.step()
          if (++uiTick % 6 === 0) setState((s) => ({ ...s, tick: sim.t }))
        }
        timer = requestAnimationFrame(loop)
      }
      loop()
    }).catch(() => { /* 받지 못하면 conn · sim 이 null 로 남고, 소비자는 빈 상태를 그립니다 */ })
    return () => { alive = false; cancelAnimationFrame(timer) }
  }, [active])

  return <RequestCtx.Provider value={request}><Ctx.Provider value={state}>{children}</Ctx.Provider></RequestCtx.Provider>
}

export function useBrain() {
  const request = useContext(RequestCtx)
  useEffect(() => request(), [request])
  return useContext(Ctx)
}
