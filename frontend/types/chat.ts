export type UIComponentType =
  | "mcq"
  | "timeslot_picker"
  | "confirmation"
  | "none";

export type MCQQuestion = {
  id: string;
  text: string;
  options: string[];
};

type UIBase<TComponent extends string, TData, TResult = unknown> = {
  component: TComponent;
  data: TData;
  state?: "active" | "completed";
  result?: TResult;
};

export type UIData =
  | UIBase<"mcq", { questions: MCQQuestion[] }, Record<string, string>>
  | UIBase<"timeslot_picker", { slots: any[] }, { selectedSlot: string }>
  | UIBase<"confirmation", { text: string }, { confirmed: boolean }>
  | {
      component: "none";
      state: undefined;
    };

export type Message = {
  role: "user" | "assistant";
  text: string;
  ui?: UIData;
};
