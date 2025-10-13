import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { WORKSPACE_MODULES } from "./modules";

export default function AppIndexPage() {
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-10 px-6 py-10">
      <header className="space-y-3">
        <p className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Workspace Overview
        </p>
        <h1 className="text-3xl font-bold md:text-4xl">
          Choose a module to get started
        </h1>
        <p className="max-w-2xl text-base text-muted-foreground">
          Access all Reg-Guru experiences from a single hub. Pick a module below
          to continue where you left off. We&apos;ll add more tools here as the
          platform grows.
        </p>
      </header>

      <section className="grid gap-6 md:grid-cols-2">
        {WORKSPACE_MODULES.map((module) => {
          const Icon = module.icon;
          return (
            <Link
              key={module.href}
              href={module.href}
              className="group flex flex-col justify-between rounded-2xl border bg-card p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-md"
            >
              <div className="flex items-start justify-between gap-4">
                <span className="inline-flex h-12 w-12 items-center justify-center rounded-full border bg-background text-primary">
                  <Icon className="h-5 w-5" />
                </span>
                <ArrowRight className="h-5 w-5 text-muted-foreground transition group-hover:translate-x-1" />
              </div>
              <div className="mt-6 space-y-2">
                <h2 className="text-lg font-semibold">{module.name}</h2>
                <p className="text-sm text-muted-foreground">
                  {module.description}
                </p>
              </div>
            </Link>
          );
        })}
      </section>
    </div>
  );
}
