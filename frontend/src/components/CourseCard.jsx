import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Globe, Lock } from "lucide-react";
import { getCourseLanguageDisplay } from "@/i18n";
import { CourseThumbnail } from "@/components/CourseThumbnail";

export const CourseCard = ({ course, showProgress = false, progress = 0 }) => {
  const navigate = useNavigate();

  return (
    <Card 
      className="bg-white border border-slate-200 rounded-sm hover:-translate-y-1 hover:shadow-md transition-all duration-200 cursor-pointer overflow-hidden"
      onClick={() => navigate(`/courses/${course.id}`)}
      data-testid={`course-card-${course.id}`}
    >
      <div className="aspect-video bg-slate-100 relative overflow-hidden">
        <CourseThumbnail
          src={course.thumbnail_url}
          alt={course.title}
          fallbackClassName="w-full h-full flex items-center justify-center bg-gradient-to-br from-[#002FA7]/10 to-[#002FA7]/5"
          fallbackIconClassName="w-12 h-12 text-[#002FA7]/40"
        />
        <div className="absolute top-2 left-2 flex gap-1">
          {course.language && (
            <Badge className="bg-[#002FA7] text-white rounded-sm text-xs">
              <Globe className="w-3 h-3 mr-1" />
              {getCourseLanguageDisplay(course.language, { short: true })}
            </Badge>
          )}
        </div>
        {course.is_private && (
          <Badge className="absolute top-2 right-2 bg-slate-800 text-white rounded-sm">
            <Lock className="w-3 h-3 mr-1" /> Private
          </Badge>
        )}
      </div>
      <CardContent className="p-4">
        <h3 className="text-lg font-medium text-[#0A0B10] mb-2 line-clamp-1">{course.title}</h3>
        <p className="text-sm text-slate-600 line-clamp-2 mb-3">{course.description}</p>
        <div className="flex items-center justify-between">
          {course.is_free ? (
            <Badge variant="secondary" className="bg-green-100 text-green-700 rounded-sm">Free</Badge>
          ) : (
            <span className="font-medium text-[#002FA7]">${course.price?.toFixed(2)}</span>
          )}
          {showProgress && (
            <div className="flex items-center gap-2">
              <Progress value={progress} className="w-20 h-2" />
              <span className="text-xs text-slate-500">{progress}%</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

