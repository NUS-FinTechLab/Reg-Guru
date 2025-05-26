import * as icons from "lucide-react";

const Icon = ({
  name,
  color,
  size,
  className,
}: {
  name: keyof typeof icons;
  color: string;
  size: number;
  className?: string;
}) => {
  const LucideIcon :any = (icons as any)[name];

  return <LucideIcon color={color} size={size} className={className} />;
};

 export default Icon