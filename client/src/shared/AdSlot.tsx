/**
 * Ad slot component.
 * Currently shows placeholder. Replace inner content with AdSense <ins> tag when ready.
 *
 * Usage:
 *   <AdSlot type="feed" />      — native card style (in feed)
 *   <AdSlot type="banner" />    — horizontal banner (between content)
 *   <AdSlot type="sidebar" />   — small square (sidebar)
 */

interface AdSlotProps {
  type: 'feed' | 'banner' | 'sidebar'
}

const STYLES: Record<string, { container: string; inner: string; label: string }> = {
  feed: {
    container: 'bg-cyber-card/50 border border-cyber-border/30 rounded-lg p-4 my-3',
    inner: 'h-24 md:h-28 rounded bg-cyber-surface/50 flex items-center justify-center',
    label: 'AD',
  },
  banner: {
    container: 'bg-cyber-card/50 border border-cyber-border/30 rounded-lg p-3 my-4',
    inner: 'h-16 md:h-20 rounded bg-cyber-surface/50 flex items-center justify-center',
    label: 'AD',
  },
  sidebar: {
    container: 'bg-cyber-card/50 border border-cyber-border/30 rounded-lg p-3 mt-4',
    inner: 'h-40 rounded bg-cyber-surface/50 flex items-center justify-center',
    label: 'AD',
  },
}

export function AdSlot({ type }: AdSlotProps) {
  const style = STYLES[type]

  return (
    <div className={style.container}>
      {/*
        TODO: Replace this placeholder with Google AdSense code:
        <ins className="adsbygoogle"
          style={{ display: 'block' }}
          data-ad-client="ca-pub-XXXXXXX"
          data-ad-slot="XXXXXXX"
          data-ad-format="auto"
          data-full-width-responsive="true" />
      */}
      <div className={style.inner}>
        <div className="text-center">
          <span className="text-[10px] text-cyber-text-dim/40 border border-cyber-text-dim/20 px-1.5 py-0.5 rounded">
            {style.label}
          </span>
          <p className="text-[10px] text-cyber-text-dim/30 mt-1">광고 영역</p>
        </div>
      </div>
    </div>
  )
}
