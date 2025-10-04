// TapPay SDK TypeScript Definitions

declare global {
  interface Window {
    TPDirect: TPDirect;
  }
}

interface TPDirect {
  setupSDK: (appId: number, appKey: string, serverType: 'sandbox' | 'production') => void;

  card: {
    setup: (config: CardSetupConfig) => void;
    onUpdate: (callback: (update: CardUpdateResult) => void) => void;
    getPrime: (callback: (result: PrimeResult) => void) => void;
    getTappayFieldsStatus: () => FieldsStatus;
  };

  linePay?: {
    getPrime: (callback: (result: LinePayPrimeResult) => void) => void;
  };

  applePay?: {
    setupMerchant: (config: ApplePayMerchantConfig) => void;
    setupPaymentRequest: (config: ApplePaymentRequest, callback: (result: ApplePayResult) => void) => void;
  };

  googlePay?: {
    setupGooglePay: (config: GooglePayConfig) => void;
    setupPaymentRequest: (config: GooglePaymentRequest, callback: (result: GooglePayResult) => void) => void;
  };
}

interface CardSetupConfig {
  fields: {
    number: FieldConfig;
    expirationDate: FieldConfig;
    ccv: FieldConfig;
  };
  styles?: string;
  isMaskCreditCardNumber?: boolean;
  maskCreditCardNumberRange?: {
    beginIndex: number;
    endIndex: number;
  };
}

interface FieldConfig {
  element: string | HTMLElement;
  placeholder: string;
}

interface CardUpdateResult {
  canGetPrime: boolean;
  hasError: boolean;
  status: {
    number: FieldStatus;
    expiry: FieldStatus;
    ccv: FieldStatus;
  };
}

interface FieldsStatus {
  canGetPrime: boolean;
  status: {
    number: FieldStatus;
    expiry: FieldStatus;
    ccv: FieldStatus;
  };
}

type FieldStatus = 0 | 1 | 2 | 3;
// 0 = 欄位為空值
// 1 = 欄位有值但格式錯誤
// 2 = 欄位有值且格式正確
// 3 = SDK 尚未準備完成

interface PrimeResult {
  status: number;
  msg: string;
  prime?: string;
  card_info?: CardInfo;
  card_secret?: {
    card_token: string;
    card_key: string;
  };
}

interface CardInfo {
  bincode: string;
  lastfour: string;
  issuer: string;
  funding: number; // 0 = 信用卡, 1 = 金融卡
  type: number; // 1 = VISA, 2 = MasterCard, 3 = JCB, 4 = Union, 5 = AMEX
  level: string;
  country: string;
  countryCode: string;
}

interface LinePayPrimeResult {
  status: number;
  msg: string;
  prime?: string;
  client_id?: string;
}

interface ApplePayMerchantConfig {
  merchantIdentifier: string;
  countryCode: string;
}

interface ApplePaymentRequest {
  total: {
    label: string;
    amount: string;
  };
  currencyCode: string;
  countryCode: string;
  supportedNetworks: string[];
  supportedCountries: string[];
  requiredBillingContactFields?: string[];
  requiredShippingContactFields?: string[];
}

interface ApplePayResult {
  status: number;
  msg: string;
  prime?: string;
}

interface GooglePayConfig {
  googleMerchantId: string;
  tappayGoogleMerchantId: string;
  allowedCardAuthMethods: string[];
  merchantName: string;
  emailRequired?: boolean;
  shippingAddressRequired?: boolean;
  billingAddressRequired?: boolean;
  shippingAddressParameters?: {
    phoneNumberRequired?: boolean;
    allowedCountryCodes?: string[];
  };
}

interface GooglePaymentRequest {
  allowedCardNetworks: string[];
  allowPrepaidCards?: boolean;
  billingAddressRequired?: boolean;
  billingAddressParameters?: {
    format?: 'MIN' | 'FULL';
    phoneNumberRequired?: boolean;
  };
  emailRequired?: boolean;
  shippingAddressRequired?: boolean;
  shippingAddressParameters?: {
    phoneNumberRequired?: boolean;
    allowedCountryCodes?: string[];
  };
  price: string;
  currency: string;
}

interface GooglePayResult {
  status: number;
  msg: string;
  prime?: string;
  total_amount?: string;
  currency?: string;
  order_id?: string;
  shippingAddress?: any;
  payerEmail?: string;
  payerPhone?: string;
}

// Payment Request Types (for backend)
export interface TapPayPaymentRequest {
  prime: string;
  amount: number;
  details: string;
  cardholder: {
    phone_number: string;
    name: string;
    email: string;
    zip_code?: string;
    address?: string;
    national_id?: string;
  };
  remember?: boolean;
  result_url?: {
    frontend_redirect_url?: string;
    backend_notify_url?: string;
  };
  three_domain_secure?: boolean;
}

export interface TapPayPaymentResponse {
  status: number;
  msg: string;
  rec_trade_id?: string;
  bank_transaction_id?: string;
  bank_order_number?: string;
  amount?: number;
  card_info?: CardInfo;
  card_secret?: {
    card_token: string;
    card_key: string;
  };
  acquirer?: string;
  millis?: number;
  bank_result_code?: string;
  bank_result_msg?: string;
}

export interface TapPayRefundRequest {
  partner_key: string;
  rec_trade_id: string;
  amount?: number; // Optional for partial refund
}

export interface TapPayRefundResponse {
  status: number;
  msg: string;
  refund_id?: string;
  refund_amount?: number;
}

export {};
