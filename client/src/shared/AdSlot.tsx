/**
 * Ad slot component — cyberpunk styled placeholder.
 * Replace inner content with AdSense <ins> tag when ready.
 */

const AD_ENABLED = true

interface AdSlotProps {
  type: 'feed' | 'banner' | 'sidebar'
}

const CONFIG: Record<string, { height: string; layout: 'horizontal' | 'vertical' }> = {
  feed: { height: 'h-24 md:h-28', layout: 'horizontal' },
  banner: { height: 'h-16 md:h-20', layout: 'horizontal' },
  sidebar: { height: 'h-44', layout: 'vertical' },
}

export function AdSlot({ type }: AdSlotProps) {
  if (!AD_ENABLED) return null

  const { height, layout } = CONFIG[type]

  return (
    <div className="my-3 rounded-lg border border-dashed border-cyber-accent/20 bg-gradient-to-r from-cyber-card via-cyber-surface/50 to-cyber-card overflow-hidden">
      <div className={`${height} flex items-center justify-center relative`}>
        {/* Scanline effect */}
        <div className="absolute inset-0 opacity-[0.03] pointer-events-none"
          style={{ backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(6,182,212,0.1) 2px, rgba(6,182,212,0.1) 4px)' }} />

        {/* Content */}
        <div className={`flex ${layout === 'horizontal' ? 'flex-row items-center gap-4' : 'flex-col items-center gap-2'} z-10`}>
          <div className="flex items-center gap-2">
            <span className="text-cyber-accent/30 text-lg">⬡</span>
            <div>
              <p className="text-[11px] text-cyber-accent/40 font-mono tracking-widest uppercase">Ad Space</p>
              <p className="text-[10px] text-cyber-text-dim/50">광고 모집중</p>
            </div>
          </div>
          <a
            href="mailto:ad@deadnetwork.society"
            className="text-[10px] text-cyber-accent/30 border border-cyber-accent/15 rounded px-2 py-0.5 hover:text-cyber-accent/60 hover:border-cyber-accent/30 transition-all"
          >
            문의하기 →
          </a>
        </div>

        {/* Corner accents */}
        <span className="absolute top-1.5 left-2 text-[8px] text-cyber-accent/15 font-mono">DNS://AD</span>
        <span className="absolute bottom-1.5 right-2 text-[8px] text-cyber-accent/15 font-mono">SLOT.{type.toUpperCase()}</span>
      </div>
    </div>
  )
}
