import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { ThumbnailUpload } from "@/components/ThumbnailUpload";
import { uploadThumbnail } from "@/lib/api";

jest.mock("@/lib/api", () => ({
  uploadThumbnail: jest.fn(),
  formatError: (error) => error.message || "error",
}));

jest.mock("@/contexts/LanguageContext", () => ({
  useLanguage: () => ({ t: (key) => key }),
}));

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

describe("ThumbnailUpload", () => {
  beforeEach(() => {
    uploadThumbnail.mockReset();
    URL.createObjectURL = jest.fn(() => "blob:http://localhost/preview");
    URL.revokeObjectURL = jest.fn();
  });

  it("calls onChange with the uploaded thumbnail URL", async () => {
    uploadThumbnail.mockResolvedValue({
      url: "/api/uploads/thumbnails/example.jpg",
    });
    const onChange = jest.fn();

    render(<ThumbnailUpload value="" onChange={onChange} />);

    const file = new File(["image"], "example.jpg", { type: "image/jpeg" });
    fireEvent.change(screen.getByTestId("course-thumbnail-upload-input"), {
      target: { files: [file] },
    });

    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith("/api/uploads/thumbnails/example.jpg");
    });
  });

  it("calls onChange with an empty string when the thumbnail is removed", async () => {
    const onChange = jest.fn();

    render(
      <ThumbnailUpload
        value="/api/uploads/thumbnails/example.jpg"
        onChange={onChange}
      />
    );

    fireEvent.click(screen.getByTestId("course-thumbnail-upload-remove"));

    expect(onChange).toHaveBeenCalledWith("");
  });

  it("shows the stored thumbnail URL in the preview", async () => {
    render(
      <ThumbnailUpload
        value="/api/uploads/thumbnails/example.jpg"
        onChange={jest.fn()}
      />
    );

    const image = screen.getByRole("img", { name: "courses.uploadThumbnail" });
    expect(image).toHaveAttribute("src", "/api/uploads/thumbnails/example.jpg");

    await act(async () => {
      image.dispatchEvent(new Event("load"));
    });
  });
});
