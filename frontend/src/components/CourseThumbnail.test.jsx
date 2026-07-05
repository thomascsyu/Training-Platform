import { act, render, screen } from "@testing-library/react";
import { CourseThumbnail } from "@/components/CourseThumbnail";

describe("CourseThumbnail", () => {
  it("renders a placeholder when no src is provided", () => {
    render(<CourseThumbnail alt="ISO 9001" testId="course-thumb" />);

    expect(screen.getByTestId("course-thumb-fallback")).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("renders an image when src is provided", () => {
    render(
      <CourseThumbnail
        src="/api/uploads/thumbnails/example.jpg"
        alt="ISO 9001"
        testId="course-thumb"
      />
    );

    const image = screen.getByRole("img", { name: "ISO 9001" });
    expect(image).toHaveAttribute("src", "/api/uploads/thumbnails/example.jpg");
  });

  it("falls back to a placeholder when the image fails to load", async () => {
    render(
      <CourseThumbnail
        src="/api/uploads/thumbnails/missing.jpg"
        alt="ISO 9001"
        testId="course-thumb"
      />
    );

    const image = screen.getByRole("img", { name: "ISO 9001" });

    await act(async () => {
      image.dispatchEvent(new Event("error"));
    });

    expect(screen.getByTestId("course-thumb-fallback")).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });
});
