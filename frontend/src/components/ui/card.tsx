"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { CometCard } from "@/components/ui/comet-card";

type CardProps = React.HTMLAttributes<HTMLDivElement> & {
  /** Effet 3D / comet au survol (désactivé sur tables denses) */
  tilt?: boolean;
};

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, tilt = false, children, ...props }, ref) => {
    const body = (
      <div
        ref={ref}
        className={cn(
          "rounded-sanad-lg border border-[var(--line)] bg-white/72 shadow-sanad-sm backdrop-blur-md transition-all duration-300",
          tilt && "hover:-translate-y-1 hover:shadow-luxe",
          className,
        )}
        {...props}
      >
        {children}
      </div>
    );

    if (!tilt) return body;
    return <CometCard className="h-full w-full">{body}</CometCard>;
  },
);
Card.displayName = "Card";

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-6", className)}
    {...props}
  />
));
CardHeader.displayName = "CardHeader";

const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn("font-display text-lg font-medium text-sanad-ink", className)}
    {...props}
  />
));
CardTitle.displayName = "CardTitle";

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
));
CardContent.displayName = "CardContent";

export { Card, CardHeader, CardTitle, CardContent };
