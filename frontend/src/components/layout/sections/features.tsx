import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Icon  from "@/components/ui/icon";
import { icons } from "lucide-react";

interface FeaturesProps {
  icon: string;
  title: string;
  description: string;
}

const featureList: FeaturesProps[] = [
  {
    icon: "FileText",
    title: "All Document Format",
    description:
      "Upload any kind of document format -- PDF, PPT, JPG, XLS etc.",
  },
  {
    icon: "Sparkle",
    title: "Smart & Accurate",
    description:
      "Reg-Guru AI Chatbot provides accurate answers for questions about your document.",
  },
  {
    icon: "Bookmark",
    title: "Save Chat & Document History",
    description:
      "YEasily review all of the documents and chats you had with Reg-Guru.",
  },
  {
    icon: "PictureInPicture",
    title: "Multi Device Support",
    description:
      "Access Reg-Guru on the go, regardless of whether you're on desktop, tablet, or smartphone.",
  },
  {
    icon: "MousePointerClick",
    title: "One click analysis",
    description:
      "Analyse any document in a single click.",
  },
  {
    icon: "Newspaper",
    title: "Understand any document",
    description:
      "Use Reg-guru chatbot AI to understand any kind of foreign document.",
  },
];

export const FeaturesSection = () => {
  return (
    <section id="features" className="container py-24 sm:py-24 px-6 lg:px-24 px-6 w-full mx-auto">
      <h2 className="text-lg text-sm font-mono uppercase text-center mb-2 tracking-wider">
        Features
      </h2>

      <h2 className="text-3xl md:text-4xl text-center font-semibold mb-4">
        What Reg-Guru does for you
      </h2>

      <h3 className="md:w-1/2 mx-auto text-lg text-center text-muted-foreground mb-8">
        Lorem ipsum dolor, sit amet consectetur adipisicing elit. Voluptatem
        fugiat, odit similique quasi sint reiciendis quidem iure veritatis optio
        facere tenetur.
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
