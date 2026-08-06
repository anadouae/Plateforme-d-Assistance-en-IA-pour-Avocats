import { cn } from "@/lib/utils";

export function BentoGrid({
  className,
  children,
}: {
  className?: string;
  children?: React.ReactNode;
}) {
  return (
    <div
      className={cn(
        "mx-auto grid max-w-6xl grid-cols-1 gap-4 md:auto-rows-[17rem] md:grid-cols-3",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function BentoGridItem({
  className,
  title,
  description,
  header,
  icon,
}: {
  className?: string;
  title?: string | React.ReactNode;
  description?: string | React.ReactNode;
  header?: React.ReactNode;
  icon?: React.ReactNode;
}) {
  return (
    <div
      className={cn(
        "group/bento row-span-1 flex flex-col justify-between space-y-4 rounded-xl border border-sanad-border bg-white p-4 shadow-sm transition duration-300 hover:shadow-luxe",
        className,
      )}
    >
      {header}
      <div className="transition duration-200 group-hover/bento:translate-x-1 rtl:group-hover/bento:-translate-x-1">
        {icon}
        <div className="mb-2 mt-2 font-display font-semibold text-sanad-navy">
          {title}
        </div>
        <div className="text-sm font-normal text-sanad-muted">{description}</div>
      </div>
    </div>
  );
}
