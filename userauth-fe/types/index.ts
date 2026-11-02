export interface IBaseResponse<TData, TErrors> {
  success: boolean;
  message: string;
  data: TData;
  errors: TErrors;
}

export interface IValidationError {
  field: string;
  message: string;
}

export interface ISuccessResponse<TData> extends IBaseResponse<TData, null> {
  success: true;
}

export interface IErrorResponse<TErrors = IValidationError[] | null> extends IBaseResponse<
  null,
  TErrors
> {
  success: false;
}

export interface IApiRequestOptions extends RequestInit {
  refreshOnUnauthorized?: boolean;
}
