export { };

/**
 * Some types can not be automatically generated from the backend. These types are defined here.
 */
declare global {

    export type PaginatedItems<T> = {
        has_more: boolean;
        items: T[];
    };
}
