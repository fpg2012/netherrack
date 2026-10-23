export function Footer({ variant = 'bottom' }: { variant?: 'bottom' | 'side' }) {
  const className = variant === 'side' ? 'side-footer' : 'site-footer'
  return (
    <footer className={className}>
      <img src="/netherrack.svg" alt="" width={16} height={16} />
      <span>
        Powered by{' '}
        <a href="https://github.com/fpg2012/netherrack" target="_blank" rel="noopener noreferrer">
          Netherrack
        </a>
      </span>
    </footer>
  )
}
