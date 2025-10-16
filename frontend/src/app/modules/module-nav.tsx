"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { cn } from "@/lib/utils";

import { WORKSPACE_MODULES } from "./modules";

export default function ModuleNav() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 shrink-0 border-r bg-card/50 backdrop-blur lg:flex lg:flex-col">
      <div className="px-6 py-5">
        <p className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Reg-Guru
        </p>
        <h1 className="text-xl font-bold leading-tight">Workspace</h1>
      </div>
      <nav className="flex-1 space-y-1 px-3 pb-6">
        {WORKSPACE_MODULES.map((module) => {
          const isActive =
            pathname === module.href || pathname.startsWith(`${module.href}/`);
          const Icon = module.icon;

          return (
            <Link
              key={module.href}
              href={module.href}
              className={cn(
                "group flex items-start gap-3 rounded-xl px-4 py-3 text-sm transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              <span className="mt-0.5 flex h-9 w-9 items-center justify-center rounded-full border bg-background">
                <Icon className="h-4 w-4" />
              </span>
              <span className="flex flex-col">
                <span className="font-medium">{module.name}</span>
                <span className="text-xs text-muted-foreground">
                  {module.description}
                </span>
              </span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

export function ModuleNavMobile() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <div className="flex gap-2 border-b bg-card/80 px-4 py-3 lg:hidden">
      {WORKSPACE_MODULES.map((module) => {
        const isActive =
          pathname === module.href || pathname.startsWith(`${module.href}/`);

        return (
          <button
            key={module.href}
            type="button"
            onClick={() => router.push(module.href)}
            className={cn(
              "rounded-full px-4 py-2 text-sm font-medium transition-colors",
              isActive
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground hover:bg-muted/80",
            )}
          >
            {module.name}
          </button>
        );
      })}
    </div>
  );
}
