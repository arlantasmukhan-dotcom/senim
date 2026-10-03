import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
import { Slot } from "radix-ui"

// SENIM buttons follow the mockups: every button is a full pill, one accent (primary),
// outline pills for secondary actions, round icon buttons for card navigation.
// Hover: a slight lift in scale plus an accent glow; press settles below 1. Reduced motion keeps the glow only.
const buttonVariants = cva(
  "inline-flex shrink-0 items-center justify-center gap-2.5 rounded-full whitespace-nowrap font-semibold outline-none select-none transition-[background-color,border-color,color,scale,box-shadow] duration-200 ease-expo hover:scale-[1.03] active:scale-[0.98] motion-reduce:hover:scale-100 focus-visible:ring-3 focus-visible:ring-ring/40 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-brand-hover hover:shadow-glow",
        outline: "border border-line-strong bg-transparent font-medium text-ink hover:border-brand hover:text-brand hover:shadow-glow-soft",
        strong: "border border-ink bg-transparent text-ink hover:bg-ink hover:text-page hover:shadow-glow",
        link: "rounded-none px-0 text-brand hover:scale-100 hover:text-brand-hover active:scale-100",
        icon: "border border-line-strong bg-transparent text-ink hover:border-brand hover:text-brand hover:shadow-glow-soft disabled:opacity-40",
        bare: "text-ink hover:bg-well disabled:opacity-40",
      },
      size: {
        default: "h-11 px-5 text-[15px]",
        lg: "h-[52px] px-[26px] text-base",
        xl: "h-14 px-7 text-[17px]",
        text: "h-auto py-2 text-[15px]",
        icon: "size-10",
        "icon-sm": "size-9",
        "icon-touch": "size-11",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant = "default",
  size = "default",
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot.Root : "button"

  return (
    <Comp
      data-slot="button"
      data-variant={variant}
      data-size={size}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
