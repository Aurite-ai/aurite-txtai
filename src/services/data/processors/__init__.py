from .general_processor import GeneralProcessor

# Import other processors as they are implemented


class ProcessorFactory:
    @staticmethod
    def get_processor(domain, txtai_client):
        if domain == "cooking":
            return GeneralProcessor(
                txtai_client
            )  # Replace with CookingProcessor when implemented
        elif domain == "gaming":
            return GeneralProcessor(
                txtai_client
            )  # Replace with GamingProcessor when implemented
        elif domain == "finance":
            return GeneralProcessor(
                txtai_client
            )  # Replace with FinanceProcessor when implemented
        elif domain == "sports":
            return GeneralProcessor(
                txtai_client
            )  # Replace with SportsProcessor when implemented
        else:
            return GeneralProcessor(txtai_client)
