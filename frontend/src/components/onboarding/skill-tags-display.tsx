import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const proficiencyVariant: Record<string, "default" | "secondary" | "outline"> = {
  EXPERT: "default", ADVANCED: "default", INTERMEDIATE: "secondary", BEGINNER: "outline",
};

interface Skill { standard_name: string; proficiency: string; evidence?: string; }

export function SkillTagsDisplay({ skills }: { skills: Skill[] }) {
  return (
    <Card>
      <CardHeader className="pb-3"><CardTitle className="text-sm">Skills</CardTitle></CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2">
          {skills.map((skill) => (
            <Badge key={skill.standard_name} variant={proficiencyVariant[skill.proficiency] ?? "outline"} title={skill.evidence} className="gap-1">
              {skill.standard_name}
              <span className="text-[10px] opacity-60">{skill.proficiency}</span>
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
