interface HorseCardSlideInProps {
  children: React.ReactNode
  index?: number
}

function HorseCardSlideIn({ children, index = 0 }: HorseCardSlideInProps) {
  return (
    <div
      className="animate-[horse-slide-in_0.55s_ease-out_both]"
      style={{ animationDelay: `${index * 0.1}s` }}
    >
      {children}
    </div>
  )
}

export default HorseCardSlideIn
