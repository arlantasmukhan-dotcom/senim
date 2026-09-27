import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
import { Slot } from "radix-ui"

// SENIM buttons follow the mockups: every button is a full pill, one accent (primary),
// outline pills for secondary actions, round icon buttons for card navigation.
const buttonVariants = cva(
  "inline-flex shrink-0 items-center justify-center gap-2.5 rounded-full whitespace-nowrap font-semibold outline-none select-none transition-[background-color,border-color,color,transform] duration-150 ease-out active:scale-[0.98] focus-visible:ring-3 focus-visible:ring-ring/40 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-brand-hover",
        outline: "border border-line-strong bg-transparent font-medium text-ink hover:border-ink",
        strong: "border border-ink bg-transparent text-ink hover:bg-ink hover:text-page",
        link: "rounded-none px-0 text-brand hover:text-brand-hover active:scale-100",
        icon: "border border-line-strong bg-transparent text-ink hover:border-ink disabled:opacity-40",
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
