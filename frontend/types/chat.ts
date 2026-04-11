type UIBase<TComponent extends string, TData> = {
  component: TComponent;
  data: TData;
};

export type PickerOption = {
  label: string;
  value: string;
  description: string;
  meta: Record<string, unknown>;
};

export type PickerData = {
  title: string;
  prompt: string;
  options: PickerOption[];
  allow_multiple: boolean;
  empty_state_message?: string;
};

export type AlertData = {
  title: string;
  message: string;
  level: "info" | "success" | "warning" | "error";
  details?: string;
};

export type UIData =
  | UIBase<"alert", AlertData>
  | UIBase<"picker", PickerData>
  | UIBase<"none", null>;

export type Message = {
  role: "user" | "assistant";
  text: string;
  ui?: UIData;
};
