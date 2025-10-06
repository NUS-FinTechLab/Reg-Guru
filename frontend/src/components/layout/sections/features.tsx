import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Icon from "@/components/ui/icon";
import { icons } from "lucide-react";

interface FeaturesProps {
  icon: string;
  title: string;
  description: string;
}

const featureList: FeaturesProps[] = [
  {
    icon: "Library",
    title: "Regulatory Knowledge",
    description:
      "Ground every answer in curated regulatory sources, guidance, and interpretations.",
  },
  {
    icon: "MessageSquare",
    title: "Contextual RAG Chat",
    description:
      "Ask follow-up questions and get citations from an assistant tuned for compliance questions.",
  },
  {
    icon: "ListChecks",
    title: "Checklist Builder",
    description:
      "Generate actionable task lists mapped to the requirements that matter to your processes.",
  },
  {
    icon: "Workflow",
    title: "Process Blueprinting",
    description:
      "Outline compliance workflows and dependencies so your team knows what comes next.",
  },
  {
    icon: "BellRing",
    title: "Change Alerts",
    description:
      "Highlight regulatory updates and revisit checklists when rules evolve.",
  },
  {
    icon: "ShieldCheck",
    title: "Team Alignment",
    description:
      "Share the same source of truth for obligations, owners, and status across the organization.",
  },
];

export const FeaturesSection = () => {
  return (
    <section id="features" className="container py-24 sm:py-24 px-6 lg:px-24 px-6 w-full mx-auto">
      <h2 className="text-lg text-sm font-mono uppercase text-center mb-2 tracking-wider">
        Features
      </h2>

      <h2 className="text-3xl md:text-4xl text-center font-semibold mb-4">
        How Reg-Guru keeps you compliant
      </h2>

      <h3 className="md:w-1/2 mx-auto text-lg text-center text-muted-foreground mb-8">
        Give your team an assistant that turns dense regulatory text into guidance, action plans, and shared accountability.
      </h3>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {featureList.map(({ icon, title, description }) => (
          <div key={title}>
            <Card className="h-full border-0 shadow-none bg-[#f1f1f1] dark:bg-[#171717]">
              <CardHeader className="flex justify-center items-center space-x-4">
                <div className="bg-blue-400 p-2 rounded-full ring-8 block ring-blue-500/10">
                  <Icon
                    name={icon as keyof typeof icons}
                    size={24}
                    color="#f1f1f1"
                    className="text-primary text-black dark:text-gray-100"
                  />
                </div>
              </CardHeader>
              <CardTitle className={"text-center uppercase font-mono"}>{title}</CardTitle>
              <CardContent className="text-muted-foreground text-center">
                {description}
              </CardContent>
            </Card>
          </div>
        ))}
      </div>
    </section>
  );
};
