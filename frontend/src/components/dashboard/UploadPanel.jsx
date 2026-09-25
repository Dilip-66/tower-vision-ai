import { useRef } from "react";
import { FileImage, RefreshCw, ScanSearch, Upload } from "lucide-react";
import { Alert } from "../ui/alert";
import { Button } from "../ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { formatFileSize } from "../../lib/format";
import { cn } from "../../lib/utils";

export function UploadPanel({
  file,
  previewUrl,
  isDragging,
  isProcessing,
  error,
  onFile,
  onDragState,
  onRun,
  onClear,
}) {
  const inputRef = useRef(null);

  const shownError = error;

  function openPicker() {
    inputRef.current?.click();
  }

  function handleFiles(fileList) {
    const next = fileList?.[0];
    if (!next) return;
    onFile(next);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload tower image</CardTitle>
        <CardDescription>Upload a field image to detect and classify telecom towers.</CardDescription>
      </CardHeader>

      <CardContent className="space-y-3">
        <input
          ref={inputRef}
          type="file"
          accept=".jpg,.jpeg,.png,.webp,.bmp,image/*"
          className="hidden"
          onChange={(event) => {
            handleFiles(event.target.files);
            event.target.value = "";
          }}
        />

        {file ? (
          <div className="space-y-3">
            <div className="overflow-hidden rounded-md border border-border bg-muted">
              <img src={previewUrl} alt="Selected tower" className="h-56 w-full object-contain" />
            </div>

            <div className="flex items-center gap-2 text-xs">
              <FileImage className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
              <span className="min-w-0 flex-1 truncate font-medium">{file.name}</span>
              <span className="shrink-0 tabular-nums text-muted-foreground">{formatFileSize(file.size)}</span>
            </div>

            <div className="flex flex-col gap-2 sm:flex-row">
              <Button onClick={onRun} disabled={isProcessing} className="flex-1">
                {isProcessing ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" aria-hidden="true" />
                    Running detection
                  </>
                ) : (
                  <>
                    <ScanSearch className="h-4 w-4" aria-hidden="true" />
                    Run detection
                  </>
                )}
              </Button>

              <Button variant="outline" onClick={openPicker} disabled={isProcessing}>
                <RefreshCw className="h-4 w-4" aria-hidden="true" />
                Replace
              </Button>
            </div>

            {!isProcessing && (
              <Button variant="ghost" size="sm" onClick={onClear} className="text-muted-foreground">
                Remove image
              </Button>
            )}
          </div>
        ) : (
          <div
            onDragOver={(event) => {
              event.preventDefault();
              onDragState(true);
            }}
            onDragLeave={() => onDragState(false)}
            onDrop={(event) => {
              event.preventDefault();
              onDragState(false);
              handleFiles(event.dataTransfer.files);
            }}
            className={cn(
              "flex flex-col items-center justify-center gap-2 rounded-md border border-dashed px-4 py-10 text-center transition-colors",
              isDragging ? "border-primary bg-secondary" : "border-input bg-background"
            )}
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-muted text-muted-foreground">
              <Upload className="h-4 w-4" aria-hidden="true" />
            </span>

            <div>
              <p className="text-sm font-medium">Drag and drop an image</p>
              <p className="mt-0.5 text-xs text-muted-foreground">or select a file from your device</p>
            </div>

            <Button variant="outline" size="sm" onClick={openPicker} className="mt-1">
              Browse files
            </Button>

            <p className="text-[11px] text-muted-foreground">JPG, PNG, WEBP, BMP · Max 15 MB</p>
          </div>
        )}

        {shownError && <Alert variant="destructive">{shownError}</Alert>}
      </CardContent>
    </Card>
  );
}
