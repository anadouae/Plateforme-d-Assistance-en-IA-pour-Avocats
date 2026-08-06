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
          "rounded-xl border border-sanad-border bg-white shadow-sm transition-shadow duration-300",
          tilt && "hover:shadow-luxe",
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
    className={cn("text-lg font-semibold text-sanad-slate", className)}
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
